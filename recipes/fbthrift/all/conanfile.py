from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools import files
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, copy
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os

required_conan_version = ">=1.52.0"

class FBThriftConan(ConanFile):
    description = """ FBThrift """
    name = "fbthrift"
    version = "2022.10.31.00"
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
        self.requires(f"fizz/{self.version}")
        self.requires(f"folly/{self.version}", transitive_headers=True)
        self.requires("boost/1.78.0")
        self.requires("bzip2/1.0.8")
        self.requires("fmt/8.0.1")
        self.requires("snappy/1.1.9")
        self.requires("libevent/2.1.12")
        self.requires("libunwind/1.5.0")
        self.requires("lz4/1.9.3")
        self.requires("libdwarf/20191104")
        self.requires("libelf/0.8.13")
        self.requires("openssl/1.1.1l")
        self.requires("xz_utils/5.2.5")
        self.requires("zlib/1.2.12")
        self.requires("zstd/1.5.2")
        self.requires("libiberty/9.1.0")

    def build_requirements(self):
        self.test_requires("gtest/1.10.0")


    def export_sources(self):
        export_conandata_patches(self)


    def source(self):
        files.get(self, **self.conan_data["sources"][self.version],
             destination=self.source_folder, strip_root=True)

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
        files.copy(self, "CODE_OF_CONDUCT.md", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        cmake = CMake(self)
        cmake.install()

        tl_cmake_dir = os.path.join(self.package_folder, "include", "thrift")
        dst_ =os.path.join(self.package_folder, "lib", "cmake", "fbthrift")
        files.copy(self, "ThriftLibrary.cmake", src=tl_cmake_dir, dst=dst_)

    @property
    def _cmake_install_base_path(self):
        return os.path.join("lib", "cmake", "protobuf")

    def package_info(self):
        fbthrift_ns = "FBThrift::"

        self.cpp_info.set_property("cmake_file_name", "fbthrift")
        self.cpp_info.set_property("cmake_target_name", f"{fbthrift_ns}fbthrift")
        self.cpp_info.includedirs.append(os.path.join("include", "libelf"))

        # bin: compiler_generate_build_templates  thrift1
        # lib/libcompiler_ast.a
        # lib/libcompiler_base.a
        # lib/libcompiler.a
        # lib/libmustache.a
        # lib/libcompiler_generators.a

        components = ["thrift-core",
            "thriftannotation",
            "thrifttyperep",
            "thrifttype",
            "thriftanyrep",
            "rpcmetadata",
            "thriftmetadata",
            "concurrency",
            "transport",
            "async",
            "thriftprotocol",
            "thrift",
            "thriftfrozen2",
            "thriftcpp2"
            ]
        deps = {
            "thrift-core" : ["fmt::fmt", "folly::folly"],

            "thriftannotation" : ["folly::folly"],
            "thrifttyperep" : ["thriftannotation"],
            "thrifttype" : ["thrifttyperep"],
            "thriftanyrep" : ["thrifttype"],

            "rpcmetadata" : ["folly::folly"],
            "thriftmetadata" : ["folly::folly"],
            "concurrency" : ["thrift-core", "rpcmetadata",
                            "openssl::openssl", "zlib::zlib", "zstd::zstd"],
            "transport" : ["concurrency"],
            "async" : ["transport", "wangle::wangle"],
            "thriftprotocol" : ["thrift-core", "async"], # "glog::glog"
            "thrift" : ["thriftprotocol"],
            "thriftfrozen2" : ["thriftmetadata", "thriftprotocol",
                                "folly::folly"], # "glog::glog", "gflag::gflag"
            "thriftcpp2" : ["thrift", "thriftfrozen2", "thriftanyrep", "rpcmetadata", "thriftmetadata", "thriftannotation"]

        }

        libs = {
            "thrift-core" : ["thrift-core"],
            "thriftannotation" : ["thriftannotation"],
            "thrifttyperep" : ["thriftannotation"],
            "thrifttype" : ["thrifttype"],
            "thriftanyrep" : ["thriftanyrep"],
            "rpcmetadata" : ["rpcmetadata"],
            "thriftmetadata" : ["rpcmetadata"],
            "concurrency" : ["concurrency"],
            "transport" : ["transport"],
            "async" : ["async"],
            "thriftprotocol" : ["thriftprotocol"],
            "thrift" : [],  # interface
            "thriftfrozen2" : ["thriftfrozen2"],
            "thriftcpp2" : ["thriftcpp2"]
        }

        for comp in components:
            self.cpp_info.components[comp].libs = libs[comp]
            self.cpp_info.components[comp].requires = deps[comp]
            self.cpp_info.components[comp].set_property("cmake_target_name", fbthrift_ns + comp)


        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)
