

init-project:
	cat required_dirs.txt | xargs mkdir -p
	cargo new grpc-demo-tonic
	
	go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest


rs-codegen:
	warp --j2 --template-file=templates/build.rs.tpl 
	--params=project_name:hello > grpc-demo-tonic/build.rs


rs-deps:
	cd grpc-demo-tonic; cargo add tonic
	cd grpc-demo-tonic; cargo add prost
	cd grpc-demo-tonic; cargo add tonic-build --build


mk-protoset:
	protoc --proto_path=grpc-demo-tonic/proto \
    --descriptor_set_out=temp_data/test.protoset \
    --include_imports test.proto


test-rpc: mk-protoset
	$(eval PROTOSET=temp_data/test.protoset)

	grpcurl -protoset $(PROTOSET) list
	grpcurl -protoset $(PROTOSET) list test.TestService
	
	grpcurl -protoset $(PROTOSET) describe test.TestService

	grpcurl -plaintext -protoset $(PROTOSET) -d '{"payload":"foobar"}' localhost:9090 test.TestService/Ping