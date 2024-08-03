const id = JSON.parse(document.getElementById('json-username').textContent);
const message_username = JSON.parse(document.getElementById('json-message-username').textContent);
const receiver = JSON.parse(document.getElementById('json-username-receiver').textContent);
const room_id = JSON.parse(document.getElementById('room-id').textContent);



function formatTime(timestamp) {
    const months = ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.'];
  
    const messageTime = new Date(timestamp);
    const month = months[messageTime.getMonth()];
    const day = messageTime.getDate();
    const year = messageTime.getFullYear();
    const hour = messageTime.getHours();
    const minute = messageTime.getMinutes();
    const period = hour >= 12 ? 'p.m.' : 'a.m.';
  
    return `${month} ${day}, ${year}, ${hour % 12 || 12}:${minute < 10 ? '0' : ''}${minute} ${period}`;
}
  
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const hostname = window.location.hostname;
const port = window.location.port ? `:${window.location.port}` : '';
const wsUrl = `${protocol}${hostname}${port}/ws/${id}/${room_id}/`;
var  socket = new WebSocket(wsUrl);

socket.onopen = function(e){
    document.querySelector('.chat_icon').style.display = 'block';
    console.log("CONNECTION ESTABLISHED");
}
socket.onclose = function(e){
    console.log(e);
}

socket.onerror = function(e){
    console.log(e);
}


socket.onmessage = function(e){
    console.log(e);
    const data = JSON.parse(e.data);
    var roomId = data.room_info.id;
    const closeConversation = data.room_info.close_conversation;
    const roomType = data.room_info.user_type;
    const sidebarDiv = document.querySelector('.left_sidebar_links');
    const existingAnchor = sidebarDiv.querySelector(`a[href="/${roomType}/chat/${roomId}/"]`);

    if (existingAnchor) {
        existingAnchor.parentNode.removeChild(existingAnchor);
    }

    const roomDiv = generateRoomDiv(data.room_info);
    let targetDiv;

    if (closeConversation) {
        targetDiv = document.querySelector('.inactive_chats.active_chats');
    } else {
        targetDiv = document.querySelector('.active_chats');
    }

    if (targetDiv && roomDiv && !document.getElementById('room_' + roomId)) {
        targetDiv.insertAdjacentHTML('afterbegin', roomDiv);
    }

    function generateRoomDiv(roomInfo) {
        // Define classes and attributes based on conditions
        let classes = "sidebar_info";
        let dataManagedBy = roomInfo.managed_by ? roomInfo.managed_by : "";
        
        if (roomInfo.managed_by) {
            classes += " managed-room";
        } else {
            classes += " unattended-room";
        }
        const roomHref = roomType === 'hha' ? `/hha/chat/${roomInfo.id}/` : roomType === 'mltc' ? `/mltc/chat/${roomInfo.id}/` : `/np/chat/${roomInfo.id}/`;
        return `
        <a href="${roomHref}">
        <div class="${classes}" data-managed-by="${dataManagedBy}" id="room_${roomInfo.id}">
          <div class="user_info_image">
             <img src="${roomInfo.image_url}" alt="user_img" class="img-fluid">
          </div>
          <div class="user_data">
             <h5>
             ${roomInfo.created_by}
             </h5>
             ${roomInfo.last_message.message_type === "text" ?
             '<p>' + roomInfo.last_message.message + '</p>' :
             roomInfo.last_message.message_type === "image" ?
             '<p>sent as an image</p>' :
             roomInfo.last_message.message_type === "video" ?
             '<p>sent as a video</p>' :
             roomInfo.last_message.message_type === "file" ?
             '<p>sent as a file</p>':
             roomInfo.last_message.message_type === "audio" ?
             '<p>sent as a audio</p>' :
             '<p>unknown message type</p>'} 
             ${roomInfo.managed_by ? `<p class="manager_name">Managed by: ${roomInfo.managed_by}</p>` : ''}

          </div>
         <div class="chat_data_right">
                <div class="chat_dropdown">
                    <div class="dropdown text-end position-relative d-flex justify-content-end align-items-center gap-3 mb-2">
                        <span class="pin_convo" ><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#000" class="bi bi-pin-fill" viewBox="0 0 16 16">
                            <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354"/>
                            </svg></span>
                        <button class="d-flex btn dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-three-dots-vertical" viewBox="0 0 16 16">
                                <path d="M9.5 13a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"></path>
                            </svg>
                        </button>
                        <ul class="dropdown-menu">
                        ${roomInfo.pin_room == false ?
                            `<li class="pinconversation" onclick="pin_conversation('${roomInfo.id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pin" viewBox="0 0 16 16">
                                    <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354m1.58 1.408-.002-.001zm-.002-.001.002.001A.5.5 0 0 1 6 2v5a.5.5 0 0 1-.276.447h-.002l-.012.007-.054.03a5 5 0 0 0-.827.58c-.318.278-.585.596-.725.936h7.792c-.14-.34-.407-.658-.725-.936a5 5 0 0 0-.881-.61l-.012-.006h-.002A.5.5 0 0 1 10 7V2a.5.5 0 0 1 .295-.458 1.8 1.8 0 0 0 .351-.271c.08-.08.155-.17.214-.271H5.14q.091.15.214.271a1.8 1.8 0 0 0 .37.282"/>
                                    </svg></span>Pin Conversation</li>`:
                            `<li class="unpin_conversation" onclick="unpin_conversation('${roomInfo.id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pin" viewBox="0 0 16 16">
                            <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354m1.58 1.408-.002-.001zm-.002-.001.002.001A.5.5 0 0 1 6 2v5a.5.5 0 0 1-.276.447h-.002l-.012.007-.054.03a5 5 0 0 0-.827.58c-.318.278-.585.596-.725.936h7.792c-.14-.34-.407-.658-.725-.936a5 5 0 0 0-.881-.61l-.012-.006h-.002A.5.5 0 0 1 10 7V2a.5.5 0 0 1 .295-.458 1.8 1.8 0 0 0 .351-.271c.08-.08.155-.17.214-.271H5.14q.091.15.214.271a1.8 1.8 0 0 0 .37.282"/>
                            </svg></span>Unpin Conversation</li>`}
                        ${roomInfo.managed_by == '' ?
                            `<li onclick="mark_conversation('${roomInfo.id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chat-left" viewBox="0 0 16 16">
                                <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
                                </svg></span> Mark as My Conversation</li>`:
                            `<li><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chat-left" viewBox="0 0 16 16">
                                    <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
                                    </svg></span> Marked Conversation</li>`}
                        ${roomInfo.close_conversation == false ?
                            `<li onclick="close_conversation('${roomInfo.id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-circle" viewBox="0 0 16 16">
                                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
                                <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708"/>
                                </svg></span> Close Conversation</li>`:
                            ''}
                        </ul>
                    </div>
                </div>

                <div class="last_active text-end">
                    <span class="d-flex align-items-center justify-content-end gap-1">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-clock" viewBox="0 0 16 16">
                            <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71z"></path>
                            <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0"></path>
                        </svg> Just Now
                    </span>
                </div>
            </div>
       </div>
    </a>`;
}
    function getMessageText(lastMessage) {
        switch (lastMessage.message_type) {
            case "text":
                return lastMessage.message;
            case "image":
                return "sent as an image";
            case "video":
                return "sent as a video";
            case "file":
                return "sent as a file";
            case "audio":
                return "sent as an audio";
            default:
                return "unknown message type";
        }
    }
    if (data.msg_type == 'image'){
        if(data.username == message_username){
            if (data.is_superuser || data.is_manager ){
                const messageTime = formatTime(data.timestamp)
                document.querySelector('#chat-body').innerHTML += `
                <div class="chat_sender">
                    <div class="chat_sender_content">
                        <a href="${data.message}" target="_blank"><img src="${data.message}" alt="uploaded image"></a>
                        <small>${messageTime}</small>
                    </div>
                </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });
                }
                else{
                    const messageTime = formatTime(data.timestamp)
                    document.querySelector('#chat-body').innerHTML += `
                    <div class="chat_sender">
                    <div class="chat_sender_content">
                        <a href="${data.message}" target="_blank"><img src="${data.message}" alt="uploaded image"></a>
                            <small>${messageTime}</small>
                    </div>
                </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true }); 
                }
        
        }else{
            if (data.is_superuser || data.is_manager ){
            const messageTime = formatTime(data.timestamp)
            document.querySelector('#chat-body').innerHTML += `
                <div class="chat_reciever">
                    <div class="chat_content">
                    <span class="sender_name">${data.full_name}[Manager]</span>
                    <a href="${data.message}" target="_blank"><img src="${data.message}" alt="uploaded image"></a>
                        <small>${messageTime}</small>
                    </div>
                </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });
            } 
            else{
                const messageTime = formatTime(data.timestamp)
                document.querySelector('#chat-body').innerHTML += `
                <div class="chat_reciever">
                    <div class="chat_content">
                    <span class="sender_name">${data.full_name}</span>
                    <a href="${data.message}" target="_blank"><img src="${data.message}" alt="uploaded image"></a>
                        <small>${messageTime}</small>
                    </div>
                </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });
            }
        
    }
}
else if (data.msg_type == 'audio'){
    if(data.username == message_username){
        if (data.is_superuser || data.is_manager ){
            const messageTime = formatTime(data.timestamp)
            document.querySelector('#chat-body').innerHTML += `
            <div class="chat_sender">
                <div class="chat_sender_content">
                <div class="sender_audio py-2">
                    <audio controls>
                        <source src="${data.message}" type="audio/ogg">
                        </audio>
                        <small>${messageTime}</small>
                    </div>
                </div>
            </div>`
            var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });
            } 
            else{
                const messageTime = formatTime(data.timestamp)
                document.querySelector('#chat-body').innerHTML += `
                <div class="chat_sender">
                <div class="chat_sender_content">
                <div class="sender_audio py-2">
                    <audio controls>
                        <source src="${data.message}" type="audio/ogg">
                        </audio>
                        <small>${messageTime}</small>
                    </div>
                </div>
            </div>`
            var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });
            }
    
    }else{
        if (data.is_superuser || data.is_manager ){
        const messageTime = formatTime(data.timestamp)
        document.querySelector('#chat-body').innerHTML += `
            <div class="chat_reciever">
                <div class="chat_content">
                <span class="sender_name">${data.full_name}[Manager]</span>
                <div class="sender_audio py-2">
                <audio controls>
                    <source src="${data.message}" type="audio/ogg">
                    </audio>
                    <small>${messageTime}</small>
                </div>
            </div>
                </div>
            </div>`
            var chatContainer = document.getElementById("chat-body");
            const observer = new MutationObserver(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });
            observer.observe(chatContainer, { childList: true });
        } 
        else{
            const messageTime = formatTime(data.timestamp)
            document.querySelector('#chat-body').innerHTML += `
            <div class="chat_reciever">
                <div class="chat_content">
                <span class="sender_name">${data.full_name}</span>
                <div class="sender_audio py-2">
                <audio controls>
                    <source src="${data.message}" type="audio/ogg">
                    </audio>
                    <small>${messageTime}</small>
                </div>
            </div>
                </div>
            </div>`
            var chatContainer = document.getElementById("chat-body");
            const observer = new MutationObserver(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });
            observer.observe(chatContainer, { childList: true });
        }
    
}
}
    else if (data.msg_type == 'file'){
        function extractFileName(url) {
            const pathname = new URL(url).pathname;
            const filename = pathname.match(/\/([^\/?#]+)$/)[1];
            return filename;
        }
        const filename = extractFileName(data.message);
            if(data.username == message_username){
                if (data.is_superuser || data.is_manager ){
                    const messageTime = formatTime(data.timestamp)
                    document.querySelector('#chat-body').innerHTML += `
                    <div class="chat_sender">
                        <div class="chat_sender_content">
                        <div class="sender_document d-flex align-items-center justify-content-between">
                        <div class="doc_info">
                        <h6 class="mb-0">${filename}</h6>
                    </div>
    
                        <span>
                            <a href="${data.message}" target="_blank">
                            <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 43 43" fill="none">
                                <path d="M37.625 0H5.375C2.40647 0 0 2.40647 0 5.375V37.625C0 40.5935 2.40647 43 5.375 43H37.625C40.5935 43 43 40.5935 43 37.625V5.375C43 2.40647 40.5935 0 37.625 0Z" fill="#898F97"/>
                                <path d="M32.0143 24.1172V28.4572C32.0143 29.0327 31.7857 29.5846 31.3787 29.9916C30.9718 30.3985 30.4198 30.6272 29.8443 30.6272H14.6544C14.0788 30.6272 13.5269 30.3985 13.12 29.9916C12.713 29.5846 12.4844 29.0327 12.4844 28.4572V24.1172" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M16.8203 18.6914L22.2453 24.1164L27.6703 18.6914" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M22.25 24.1166V11.0967" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            </a>
                        </span>
                </div>
                        <small>${messageTime}</small>
                        </div>
                    </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });   
                }
                else{
                    const messageTime = formatTime(data.timestamp)
                    document.querySelector('#chat-body').innerHTML += `
                    
                <div class="chat_sender">
                    <div class="chat_sender_content">
                    <div class="sender_document d-flex align-items-center justify-content-between">
                    <div class="doc_info">
                    <h6 class="mb-0">${filename}</h6>
                </div>

                    <span>
                        <a href="${data.message}" target="_blank">
                        <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 43 43" fill="none">
                            <path d="M37.625 0H5.375C2.40647 0 0 2.40647 0 5.375V37.625C0 40.5935 2.40647 43 5.375 43H37.625C40.5935 43 43 40.5935 43 37.625V5.375C43 2.40647 40.5935 0 37.625 0Z" fill="#898F97"/>
                            <path d="M32.0143 24.1172V28.4572C32.0143 29.0327 31.7857 29.5846 31.3787 29.9916C30.9718 30.3985 30.4198 30.6272 29.8443 30.6272H14.6544C14.0788 30.6272 13.5269 30.3985 13.12 29.9916C12.713 29.5846 12.4844 29.0327 12.4844 28.4572V24.1172" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M16.8203 18.6914L22.2453 24.1164L27.6703 18.6914" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M22.25 24.1166V11.0967" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </a>
                    </span>
            </div>
                    <small>${messageTime}</small>
                    </div>
                </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });
                }
            
            }else{
                if (data.is_superuser || data.is_manager ){
                    const messageTime = formatTime(data.timestamp)
                    document.querySelector('#chat-body').innerHTML += `
                
                    <div class="chat_reciever">
                        <div class="chat_content">
                        <span class="sender_name">${data.full_name}[Manager]</span>
                        <div class="sender_document d-flex align-items-center justify-content-between">
                        <div class="doc_info">
                        <h6 class="mb-0">${filename}</h6>
                    </div>
    
                        <span>
                            <a href="${data.message}" target="_blank">
                            <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 43 43" fill="none">
                                <path d="M37.625 0H5.375C2.40647 0 0 2.40647 0 5.375V37.625C0 40.5935 2.40647 43 5.375 43H37.625C40.5935 43 43 40.5935 43 37.625V5.375C43 2.40647 40.5935 0 37.625 0Z" fill="#898F97"/>
                                <path d="M32.0143 24.1172V28.4572C32.0143 29.0327 31.7857 29.5846 31.3787 29.9916C30.9718 30.3985 30.4198 30.6272 29.8443 30.6272H14.6544C14.0788 30.6272 13.5269 30.3985 13.12 29.9916C12.713 29.5846 12.4844 29.0327 12.4844 28.4572V24.1172" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M16.8203 18.6914L22.2453 24.1164L27.6703 18.6914" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M22.25 24.1166V11.0967" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            </a>
                        </span>
                </div>
                        <small>${messageTime}</small>
                        </div>
                    </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });   
                }
                else{
                    const messageTime = formatTime(data.timestamp)
                    document.querySelector('#chat-body').innerHTML += `
                    
                <div class="chat_reciever">
                    <div class="chat_content">
                    <span class="sender_name">${data.full_name}</span>
                    <div class="sender_document d-flex align-items-center justify-content-between">
                    <div class="doc_info">
                    <h6 class="mb-0">${filename}</h6>
                </div>

                    <span>
                        <a href="${data.message}" target="_blank">
                        <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 43 43" fill="none">
                            <path d="M37.625 0H5.375C2.40647 0 0 2.40647 0 5.375V37.625C0 40.5935 2.40647 43 5.375 43H37.625C40.5935 43 43 40.5935 43 37.625V5.375C43 2.40647 40.5935 0 37.625 0Z" fill="#898F97"/>
                            <path d="M32.0143 24.1172V28.4572C32.0143 29.0327 31.7857 29.5846 31.3787 29.9916C30.9718 30.3985 30.4198 30.6272 29.8443 30.6272H14.6544C14.0788 30.6272 13.5269 30.3985 13.12 29.9916C12.713 29.5846 12.4844 29.0327 12.4844 28.4572V24.1172" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M16.8203 18.6914L22.2453 24.1164L27.6703 18.6914" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M22.25 24.1166V11.0967" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </a>
                    </span>
            </div>
                    <small>${messageTime}</small>
                    </div>
                </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });
                }
                
            }
        
        
    }
    else if (data.msg_type == 'video'){
        if(data.username == message_username){
            if (data.is_superuser || data.is_manager ){
                const messageTime = formatTime(data.timestamp)  
                document.querySelector('#chat-body').innerHTML += `
                <div class="chat_sender">
                    <div class="chat_sender_content">
                        <video width="320" height="240" controls>
                            <source src="${data.message}" type="video/mp4">
                        </video>
                            <small>${messageTime}</small>
                    </div>
                </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });
                }
                else{
                const messageTime = formatTime(data.timestamp)  
                document.querySelector('#chat-body').innerHTML += `
                <div class="chat_sender">
                    <div class="chat_sender_content">
                        <video width="320" height="240" controls>
                            <source src="${data.message}" type="video/mp4">
                        </video>
                            <small>${messageTime}</small>
                    </div>
                </div>`
                var chatContainer = document.getElementById("chat-body");
                const observer = new MutationObserver(() => {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });
                observer.observe(chatContainer, { childList: true });
                }
        }else{
            if (data.is_superuser || data.is_manager ){
            const messageTime = formatTime(data.timestamp)  
            document.querySelector('#chat-body').innerHTML += `
            <div class="chat_reciever">
                <div class="chat_content">
                <span class="sender_name">${data.full_name}[Manager]</span>
                <video width="320" height="240" controls>
                <source src="${data.message}" type="video/mp4">
            </video>
                    <small>${messageTime}</small>
                </div>
            </div>`
            var chatContainer = document.getElementById("chat-body");
            const observer = new MutationObserver(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });
            observer.observe(chatContainer, { childList: true });
            }
            else{
            const messageTime = formatTime(data.timestamp)  
            document.querySelector('#chat-body').innerHTML += `
            <div class="chat_reciever">
                <div class="chat_content">
                <span class="sender_name">${data.full_name}</span>
                <video width="320" height="240" controls>
                <source src="${data.message}" type="video/mp4">
            </video>
                    <small>${messageTime}</small>
                </div>
            </div>`
            var chatContainer = document.getElementById("chat-body");
            const observer = new MutationObserver(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });
            observer.observe(chatContainer, { childList: true });
            }

        }
    
    
}

    else if ( data.msg_type == "text"){
    if(data.username === message_username){
        const messageTime = formatTime(data.timestamp)
        document.querySelector('#chat-body').innerHTML += `
        <div class="chat_sender">
            <div class="chat_sender_content">
                <p>
                ${data.message}
                </p>
                    <small>${messageTime}</small>
            </div>
        </div>`
        var chatContainer = document.getElementById("chat-body");
        const observer = new MutationObserver(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
        observer.observe(chatContainer, { childList: true });
    }else{
        if (data.is_superuser || data.is_manager ){
            const messageTime = formatTime(data.timestamp)
            document.querySelector('#chat-body').innerHTML += `
            <div class="chat_reciever">
                <div class="chat_content">
                <span class="sender_name">${data.full_name} [Manager]</span>
                    <p class="member_bg">
                    ${data.message}
                    </p>
                        <small>${messageTime}</small>
                </div>
            </div>`
            var chatContainer = document.getElementById("chat-body");
            const observer = new MutationObserver(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });
            observer.observe(chatContainer, { childList: true });
        }
        else{
        const messageTime = formatTime(data.timestamp)
        document.querySelector('#chat-body').innerHTML += `
        <div class="chat_reciever">
            <div class="chat_content">
            <span class="sender_name">${data.full_name}</span>
                <p>
                ${data.message}
                </p>
                <small>${messageTime}</small>
            </div>
        </div>`
        var chatContainer = document.getElementById("chat-body");
        const observer = new MutationObserver(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
        observer.observe(chatContainer, { childList: true });
        }
        
    }
}
}
document.querySelector('#chat-message-submit').onclick = function(e){
    const message_input = document.querySelector('#message_input');
    const message = message_input.value;

    socket.send(JSON.stringify({
        'message':message,
        'username':message_username,
        'receiver':receiver,
        'msg_type':'text'
    }));

    message_input.value = '';
}

document.querySelector('#message_input').onkeydown = function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
       e.preventDefault(); 
       document.querySelector('#chat-message-submit').click();
       return false;
    }
 };



function openFileInput() {
    document.getElementById('fileInput').click();
  }


function categorizeFileType(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    if (['png', 'jpg', 'jpeg', 'gif', 'bmp'].includes(extension)) {
        return 'image';
    } else if (['mp4', 'avi', 'mov', 'mkv'].includes(extension)) {
        return 'video';
    } else {
        return 'file';
    }
}
function handleFileUpload(input) {
const selectedFile = input.files[0];

    if (selectedFile) {
        const fileType = categorizeFileType(selectedFile.name);

        switch (fileType) {
            case 'image':
                sendImage(selectedFile);
                break;
            case 'video':
                sendVideo(selectedFile);
                break;
            case 'file':
                sendFile(selectedFile);
                break;
            default:
                console.error('Unsupported file type');
        }
    }
}

   
function sendImage(file) {
    var formData = new FormData();
    formData.append('file', file);   
    fetch('/upload-image/', {
    method: 'POST',
    headers: {
       'X-CSRFToken': getCookie('csrftoken'),
    },
    body: formData
    })
    .then(response => response.json())
    .then(data => {
       
       socket.send(JSON.stringify({
          'message': data,
          'username':message_username,
          'receiver':receiver,
          'msg_type':'image'
       }));
  
    })
    .catch(error => {
       console.error('Error:', error);
    });
  }

function sendVideo(file) {
    var formData = new FormData();
    formData.append('file', file);   
    fetch('/upload-image/', {
    method: 'POST',
    headers: {
       'X-CSRFToken': getCookie('csrftoken'),
    },
    body: formData
    })
    .then(response => response.json())
    .then(data => {
       socket.send(JSON.stringify({
          'message': data,
          'username':message_username,
          'receiver':receiver,
          'msg_type':'video'
       }));
  
    })
    .catch(error => {
       console.error('Error:', error);
    });
  }

function sendFile(file) {
    var formData = new FormData();
    formData.append('file', file);   
    fetch('/upload-image/', {
    method: 'POST',
    headers: {
       'X-CSRFToken': getCookie('csrftoken'),
    },
    body: formData
    })
    .then(response => response.json())
    .then(data => {
       socket.send(JSON.stringify({
          'message': data,
          'username':message_username,
          'receiver':receiver,
          'msg_type':'file'
       }));
  
    })
    .catch(error => {
       console.error('Error:', error);
    });
  }
 
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
       var cookies = document.cookie.split(';');
       for (var i = 0; i < cookies.length; i++) {
          var cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
          }
       }
    }
    return cookieValue;
  }



function close_conversation(roomID){
    event.preventDefault();
    $.ajax({
        type: 'GET',
        url: '/close_conversation/',  
        data: {
            roomId: roomID
        },
        success: function(response) {
            console.log(response)
            const close_message = "Thank you for reaching out to us today. It was a pleasure assisting you. Should you have any other questions or concerns in the future, please don't hesitate to contact us. Have a great day!"

            socket.send(JSON.stringify({
                'message':close_message,
                'username':message_username,
                'receiver':receiver,
                'msg_type':'text'
            }));
            

        },
        error: function(error) {
            console.error('Error closing conversation:', error);
        }
    });  
}




// var shouldClose = false;
// var connectionEstablished = false; // Track if the connection has been established after being closed
// var idleTimeout; // Variable to store the timeout ID

// function checkAndCloseSocket() {
//     if (shouldClose) {
//         // console.log("inside closing sockets----------", shouldClose);
//         notify_socket.close(1000, 'Closing due to inactivity');
//     } else {
//         // console.log("inside else--------", notify_socket.readyState, notify_socket.readyState === 3);
//         if (notify_socket.readyState === 3 && !connectionEstablished) {
//             let event = new Event('open');
//             notify_socket.onopen(event);
//             connectionEstablished = true; // Set connectionEstablished to true after establishing connection
//         }
//     }
// }

// function startIdleTimer() {
//     // console.log("isnide startIdleTimer")
//     if(shouldClose==false){
//         // console.log("calling checkAndCloseSocket",shouldClose);
//         shouldClose = true;
//         checkAndCloseSocket();
//     }
// }

// setTimeout(() => {
//     startIdleTimer()
// }, 200000);

// function resetIdleTimeout() {
//     // console.log("inside resetIdleTimeout function", shouldClose);
//     if (shouldClose == true) {
//         shouldClose = false;
//         clearTimeout(idleTimeout);
//     }
//     checkAndCloseSocket();
// }

// // Add event listeners for various user interactions
// window.addEventListener('mousemove', resetIdleTimeout);
// window.addEventListener('keydown', resetIdleTimeout);
// window.addEventListener('click', resetIdleTimeout);
// window.addEventListener('scroll', resetIdleTimeout);
// window.addEventListener('touchstart', resetIdleTimeout);

// // Initial call to set the timeout
// resetIdleTimeout();
