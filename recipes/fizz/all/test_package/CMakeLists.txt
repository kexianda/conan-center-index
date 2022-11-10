cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

find_package(fizz REQUIRED CONFIG)
find_package(folly REQUIRED)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME}
    fizz::fizz Folly::folly)


if (${FIZZ_VERSION} VERSION_LESS "2020.08.31.00")
    set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 14)
else()
    set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 17)
endif()
