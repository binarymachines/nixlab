
//
// Generated Rust file for grpc
//

use {{ config.pkg_name }}::{{ config.pkg_name }}_service_server::{ {{ config.svc_name }}, {{ config.svc_name}}Server};

{% for msg_type in config.messages %}
use {{ config.pkg_name}}::{ {{msg_type}} };
{% endfor %}

use std::net::SocketAddr;
use tonic::{Request, Response, Status, transport::Server};
use anyhow::Result;

pub mod {{config.pkg_name}} {
    tonic::include_proto!("{{config.pkg_name}}");
}

#[derive(Default)]
pub struct ServiceImpl {}

#[tonic::async_trait]
impl TestService for ServiceImpl {
    async fn ping (&self, request: Request<PingRequest>) -> std::result::Result<Response<PingResponse>, Status> {
        let reply = PingResponse {
            payload: format!("server received message {}.", request.into_inner().payload),
        };

        Ok(Response::new(reply))
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let addr: SocketAddr = "127.0.0.1:9090".parse()?;
    let svc = ServiceImpl::default();

    Server::builder()
        .add_service(TestServiceServer::new(svc))
        .serve(addr)
        .await?;

    Ok(())
}