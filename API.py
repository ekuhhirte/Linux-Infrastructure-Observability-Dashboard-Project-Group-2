import asyncio

class AsyncAPIServer:
	async def start(self):
		# Start up the async TCP server and it to listen forever

		# ip address of '0.0.0.0' is a wildcard to support any incoming IP, port is 8888
		# port can be changed as needed
		server = await asyncio.start_server(self.handle_client, '0.0.0.0', 8888) 
		
		addr = server.sockets[0].getsockname()
		print(f"TCP Server listening on {addr}")

		async with server:
			# tells the event loop to keep scheduling the TCP server untill the program is no longer running
			await server.serve_forever() 

if __name__ == "__main__": #only runs if this is the host file and not being called as an import
	server_instance = AsyncAPIServer()
	try:
		asyncio.run(server_instance.start()) # calls the async start function which boots the server
	except KeyboardInterrupt:
		print("\nSerer Shutting Down manually.")
		# Add a async closer function here if needed.