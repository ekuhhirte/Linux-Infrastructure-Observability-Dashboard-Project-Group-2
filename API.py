import asyncio

class AsyncAPIServer:
	async def start(self):
		# Start up the async TCP server and it to listen forever

		# Ip address of '0.0.0.0' is a wildcard to support any incoming IP, port is 8888
		# Port can be changed as needed
		server = await asyncio.start_server(self.handle_client, '0.0.0.0', 8888) 
		
		addr = server.sockets[0].getsockname()
		print(f"TCP Server listening on {addr}") # Basic debug statements

		async with server:
			# Tells the event loop to keep scheduling the TCP server untill the program is no longer running
			await server.serve_forever() 
	
	async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
		addr = writer.get_extra_info('peername')
		print(f"New connection (inbound) from {addr}") # Basic debug statements

		try:
			while True:
				# Read TCP chunks up to a newline character delimiter (which is inserted by the client to mark the end of the message)
				# This code will keep going back to await the next message
				data = await reader.readline() #queues the next line read in the event loop
				if not data:
					print(f"Connection (inbound) from {addr} disconnected") # Basic debug statements
					break 

				message = data.decode.strip()
				print(f"Recieved message from {addr}: {message}") # Basic debug statement

				returnMessage = f"Echo: {message}\n".encode()
				writer.write(returnMessage) # Send back an echo of the message recieved for debug purposes

				# Convert payload here and call await functions, take their answer and respond back
		except asyncio.CancelledError:
			pass 
		except Exception as e:
			print(f"Error handling client (inbound) from {addr}") # Basic debug statements
		finally:
			writer.close()
			await writer.wait_closed() # Closes the connection and waits for it to close



if __name__ == "__main__": #only runs if this is the host file and not being called as an import
	server_instance = AsyncAPIServer()
	try:
		asyncio.run(server_instance.start()) # calls the async start function which boots the server
	except KeyboardInterrupt:
		print("\nSerer Shutting Down manually.")
		# Add a async closer function here if needed.