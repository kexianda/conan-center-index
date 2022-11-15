from conan import ConanFile
from conan.tools import files
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, copy
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os

required_conan_version = ">=1.52.0"

class ProxygenConan(ConanFile):
    description = """ Proxygen """
    name = "proxygen"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "simd_level": [None, "sse4.2", "avx", "avx2"]
    }

    default_options = {
        "shared": False,
        "simd_level" : "avx2"
    }

    def requirements(self):
        self.requires(f"wangle/{self.version}")

    def build_requirements(self):
        self.test_requires("gtest/1.11.0")

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        files.get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=False)

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
        if self.settings.arch not in ["x86", "x86_64"]:
            del self.options.simd_level

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        if self.options.shared:
            self.options["glib"].shared = True

    @property
    def _minimum_cpp_standard(self):
        return 17

    @property
    def _minimum_compilers_version(self):
        return {
            "gcc": "7",
            "Visual Studio": "16",
            "clang": "6",
            "apple-clang": "10",
        }

    def validate(self):
        if self.info.settings.compiler.cppstd:
            check_min_cppstd(self, "17")

        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warn("{} recipe lacks information about the {} compiler support.".format(self.name, self.settings.compiler))
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration("{} requires C++{} support. The current compiler {} {} does not support it.".format(
                    self.name, self._minimum_cpp_standard, self.settings.compiler, self.settings.compiler.version))

        if self.settings.os in ["Macos", "Windows"]:
            raise ConanInvalidConfiguration("Not be tested on {} yet. ".format(self.settings.os))

    def layout(self):
        cmake_layout(self, build_folder='_build')

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        if self.options.simd_level is not None:
            if not is_msvc(self):
                opts = f"-m{self.options.simd_level} -mfma"
                tc.variables["CMAKE_C_FLAGS"] = opts
                tc.variables["CMAKE_CXX_FLAGS"] = opts
            else:
                opts = f"/arch:{self.options.simd_level.upper()} /arch:FMA"
                tc.variables["CMAKE_C_FLAGS"] = opts
                tc.variables["CMAKE_CXX_FLAGS"] = opts
        tc.generate()

        CMakeDeps(self).generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        files.copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        files.copy(self, "README", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        files.copy(self, "CONTRIBUTING.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "proxygen")
        self.cpp_info.set_property("cmake_target_name", "proxygen::proxygen")

        self.cpp_info.components["proxygen"].libs = ["proxygen"]
        self.cpp_info.components["proxygen"].set_property("cmake_target_name", "proxygen::proxygen")

        self.cpp_info.components["proxygenhttpserver"].libs = ["proxygenhttpserver"]
        self.cpp_info.components["proxygenhttpserver"].requires = ["proxygen"]
        self.cpp_info.components["proxygenhttpserver"].set_property("cmake_target_name", "proxygen::proxygenhttpserver")

        self.cpp_info.components["proxygencurl"].libs = ["proxygencurl"]
        self.cpp_info.components["proxygencurl"].requires = ["proxygen"]
        self.cpp_info.components["proxygencurl"].set_property("cmake_target_name", "proxygen0.::proxygen")

        # TODO: to remove in conan v2 once cmake_find_package_* & pkg_config generators removed
        self.cpp_info.components["proxygen"].names["cmake_find_package"] = "proxygen"
        self.cpp_info.components["proxygen"].names["cmake_find_package_multi"] = "proxygen"
        self.cpp_info.components["proxygenhttpserver"].names["cmake_find_package"] = "proxygenhttpserver"
        self.cpp_info.components["proxygenhttpserver"].names["cmake_find_package_multi"] = "proxygenhttpserver"
        self.cpp_info.components["proxygencurl"].names["cmake_find_package"] = "proxygencurl"
        self.cpp_info.components["proxygencurl"].names["cmake_find_package_multi"] = "proxygencurl"
