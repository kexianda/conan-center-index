from conan import ConanFile
from conan.tools import files
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, copy
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os

required_conan_version = ">=1.52.0"

class FizzConan(ConanFile):
    description = """ Fizz is a TLS 1.3 implementation. """
    name = "fizz"
    version = "2022.10.31.00"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "simd_level": [None, "sse4.2", "avx", "avx2"]
    }
    default_options = {
        "shared": False,
        "folly:use_sse4_2": True,
        "simd_level" : "avx2"
    }

    def requirements(self):
        self.requires(f"folly/{self.version}")
        self.requires("boost/1.78.0")
        self.requires("openssl/1.1.1l")
        self.requires("glog/0.4.0")
        self.requires("gflags/2.2.2")

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
        return 17 if Version(self.version) >= "2020.08.31.00" else 14

    @property
    def _minimum_compilers_version(self):
        return {
            "Visual Studio": "15",
            "gcc": "5",
            "clang": "6",
            "apple-clang": "8",
        } if self._minimum_cpp_standard == 14 else {
            "gcc": "7",
            "Visual Studio": "16",
            "clang": "6",
            "apple-clang": "10",
        }

    def validate(self):
        if self.info.settings.compiler.cppstd:
            check_min_cppstd(self, "14")

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
        cmake.configure(build_script_folder=os.path.join(self.source_folder, "fizz"))
        cmake.build()

    def package(self):
        files.copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        files.copy(self, "README", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        files.copy(self, "CODE_OF_CONDUCT.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        files.copy(self, "logo2x.png", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        files.copy(self, "CONTRIBUTING.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "fizz")
        self.cpp_info.set_property("cmake_target_name", "fizz::fizz")

        self.cpp_info.components["fizz"].libs = ["fizz"]
        self.cpp_info.components["fizz"].set_property("cmake_target_name", "fizz::fizz")

        self.cpp_info.components["fizz_test_support"].libs = ["fizz_test_support"]
        self.cpp_info.components["fizz_test_support"].requires = ["fizz"]
        self.cpp_info.components["fizz_test_support"].set_property("cmake_target_name", "fizz::fizz_test_support")
