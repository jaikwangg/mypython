message = input()
codedMessage = input()


refMessage = ''
for i in range(len(message)):
    if message[i] != ' ' and refMessage.find(message[i]) == -1:
        refMessage = refMessage + message[i]


newCodedMessage = input()

for i in range(len(newCodedMessage)):
    refIndex = codedMessage.find(newCodedMessage[i])
    if refIndex > -1:
        print(refMessage[refIndex],end = '')
    else:
        print(newCodedMessage[i],end = '')
message = "the quick brown fox jumps over the lazy dog"
coded_message = "ldt gsxva nkjqi zjm hsbpu jctk ldt ryfw oje"