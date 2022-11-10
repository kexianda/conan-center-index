cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

find_package(wangle REQUIRED CONFIG)
find_package(folly REQUIRED CONFIG)

get_target_property(var wangle::wangle INTERFACE_LINK_LIBRARIES)

add_executable(${PROJECT_NAME} test_package.cpp)
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_17)
target_link_libraries(${PROJECT_NAME}
    PUBLIC wangle::wangle Folly::folly)


