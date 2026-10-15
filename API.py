import asyncio
import json

PIPELINE_PATH = "/tmp/hardware_stats.fifo"
host = "0.0.0.0" # Listen on all interfaces, let the firewall handle sorting out who should connect or not
port = 5000 #Port for TCP clients to connect to

class AsyncAPIServer:
	async def start(self):
		# Start up the async TCP server and it to listen forever

		# Ip address of '0.0.0.0' is a wildcard to support any incoming IP, port is 8888
		# Port can be changed as needed
		server = await asyncio.start_server(self.handle_client, host, port) 
		
		addr = server.sockets[0].getsockname()
		print(f"TCP Server listening on {addr}:{port}") # Basic debug statements

		async with server:
			# Tells the event loop to keep scheduling the TCP server untill the program is no longer running
			await server.serve_forever() 

	
	async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
		addr = writer.get_extra_info('peername')
		print(f"New connection (inbound) from {addr}") # Basic debug statements

		try:
			#open pipeline
			pipeline = open(PIPELINE_PATH, "r", buffering=1)
			print("Pipeline opened successfully. Streaming data to client...")

			while True:
				line = pipeline.readline()
				if not line:
					# writer disconnected or pipe closed
					print("Pipe stream closed. Closing connection") # not sure if this is right escalation
					break

				writer.write(line.encode("utf-8"))
				await writer.drain() #ensure that data is completly flushed to the socket
		except (ConnectionResetError, BrokenPipeError):
			print("Client disconnected")	
		except asyncio.CancelledError:
			pass 
		except Exception as e:
			print(f"Error handling client (inbound) from {addr}") # Basic debug statements
		finally:
			if pipeline:
				pipeline.close()
			writer.close()
			await writer.wait_closed() # Closes the connection and waits for it to close
			print("Ready for next client connection...")

	

if __name__ == "__main__": #only runs if this is the host file and not being called as an import
	server_instance = AsyncAPIServer()
	try:
		asyncio.run(server_instance.start()) # calls the async start function which boots the server
	except KeyboardInterrupt:
		print("\nServer Shutting Down manually.")
		# Add a async closer function here if needed.