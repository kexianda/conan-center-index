#include <cstdlib>
#include <iostream>
#include <fizz/client/ClientProtocol.h>
#include <fizz/client/FizzClientContext.h>


int main() {
    auto context_ = std::make_shared<fizz::client::FizzClientContext>();
    assert(context_ != nullptr);
    return EXIT_SUCCESS;
}
