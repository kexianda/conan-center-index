#include "wangle/bootstrap/ClientBootstrap.h"
#include "wangle/bootstrap/ServerBootstrap.h"
#include "wangle/channel/Handler.h"

#include <folly/String.h>
// namespace wangle;
// using namespace folly;

typedef wangle::Pipeline<folly::IOBufQueue&, std::unique_ptr<folly::IOBuf>> BytesPipeline;

typedef wangle::ServerBootstrap<BytesPipeline> TestServer;
typedef wangle::ClientBootstrap<BytesPipeline> TestClient;

int main() {
    TestServer server;
    TestClient client;
    return EXIT_SUCCESS;
}
