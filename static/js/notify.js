
const notify_protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const notify_hostname = window.location.hostname;
const notify_port = window.location.port ? `:${window.location.port}` : '';
const notify_wsUrl = `${notify_protocol}${notify_hostname}${notify_port}/ws/notify/`;
var notify_socket = new WebSocket(notify_wsUrl);

var shouldClose=false;
var idleTimeout; // Variable to store the timeout ID

notify_socket.onopen = function(e){
    console.log("Notification CONNECTION ESTABLISHED");

}

notify_socket.onclose = function(e){
    console.log(e);
}

notify_socket.onerror = function(e){
    console.log(e);
}

notify_socket.onmessage = function(e){
    const data = JSON.parse(e.data);
    if (data.play_sound){
        var firstsound = new Audio('/static/first_notification_sound.mp3');
        firstsound.load();
        firstsound.play();
    }
    else{
        var mySound = new Audio('/static/notification-sound.mp3');
        mySound.load();
        mySound.play();
    }

    if (data.room_information.room_type === 'hha') {
        const hha_countBadge = document.getElementById('hha_count_badge');
        if (hha_countBadge) {
            const currentCount = parseInt(hha_countBadge.textContent, 10) || 0;
            hha_countBadge.textContent = currentCount + 1;
        }
        let li_data = `<li>
        <button onclick="hha_notification('${data.room_information.room_id}')">
        ${data.sender_name} ${data.message}
        </button>
        </li>`
        document.getElementById("hha_notification_inner").innerHTML = li_data;
   

        const existingAnchor = document.querySelector(`a[href="/hha/chat/${data.room_information.room_id}/"]`);

        if (existingAnchor) {
            existingAnchor.parentNode.removeChild(existingAnchor);
        }

        let user_data = `
        <a href="/hha/chat/${data.room_information.room_id}/">
         <div class="sidebar_info d-flex active-bg">
           <div class="user_info_image">
              <img src="${data.image_url}" alt="user_img" class="img-fluid">
           </div>
           <div class="user_data">
              <h5>
              ${data.sender_name}
              </h5>
           
              ${data.room_information.message_type === "text" ?
                '<p><strong>' + data.room_information.last_message + '</strong></p>' :
                data.room_information.message_type === "image" ?
                '<p><strong>sent as an image</strong></p>' :
                data.room_information.message_type === "video" ?
                '<p><strong>sent as a video</strong></p>' :
                data.room_information.message_type === "file" ?
                '<p><strong>sent as a file</strong></p>':
                data.room_information.message_type === "audio" ?
                '<p><strong>sent as a audio</strong></p>' :
                '<p><strong>unknown message type</strong></p>'} 
           </div>
          <div class="chat_data_right">
                                                    <div class="chat_dropdown">
                                                    <span class="badge rounded-pill text-bg-success">${data.room_information.hha_room_unread_count } </span>
                                                        <div class="dropdown text-end position-relative d-flex justify-content-end align-items-center gap-3 mb-2">
                                                            <span class="pin_convo"  style="display:none"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#000" class="bi bi-pin-fill" viewBox="0 0 16 16">
                                                                <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354"/>
                                                              </svg></span>
                                                            <button class="d-flex btn dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-three-dots-vertical" viewBox="0 0 16 16">
                                                                    <path d="M9.5 13a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"></path>
                                                                </svg>
                                                            </button>
                                                            <ul class="dropdown-menu">
                                                                 <li class="pinconversation" onclick="pin_conversation('${data.room_information.room_id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pin" viewBox="0 0 16 16">
                                                                        <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354m1.58 1.408-.002-.001zm-.002-.001.002.001A.5.5 0 0 1 6 2v5a.5.5 0 0 1-.276.447h-.002l-.012.007-.054.03a5 5 0 0 0-.827.58c-.318.278-.585.596-.725.936h7.792c-.14-.34-.407-.658-.725-.936a5 5 0 0 0-.881-.61l-.012-.006h-.002A.5.5 0 0 1 10 7V2a.5.5 0 0 1 .295-.458 1.8 1.8 0 0 0 .351-.271c.08-.08.155-.17.214-.271H5.14q.091.15.214.271a1.8 1.8 0 0 0 .37.282"/>
                                                                      </svg></span>Pin Conversation</li>
                                                                <li onclick="mark_conversation('${data.room_information.room_id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chat-left" viewBox="0 0 16 16">
                                                                    <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
                                                                  </svg></span> Mark as My Conversation</li>
                                                                <li onclick="close_conversation('${data.room_information.room_id}')><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-circle" viewBox="0 0 16 16">
                                                                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
                                                                    <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708"/>
                                                                  </svg></span> Close Conversation</li>
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
     </a>
     </div>`
        hha_sidebar = document.querySelector("#hha_sidebar")  
        targetDiv = hha_sidebar.querySelector('.active_chats');
        targetDiv.insertAdjacentHTML('afterbegin', user_data);
    }
    if (data.room_information.room_type === 'mltc') {
        const mltc_countBadge = document.getElementById('mltc_count_badge');
        if (mltc_countBadge) {
            const currentCount = parseInt(mltc_countBadge.textContent, 10) || 0;
            mltc_countBadge.textContent = currentCount + 1;
        }
        let li_data = `<li>
        <button onclick="mltc_notification('${data.room_information.room_id}')">
        ${data.sender_name} ${data.message}
        </button>
        </li>`

        document.getElementById("mltc_notification_inner").innerHTML = li_data;
        
        const existingAnchor = document.querySelector(`a[href="/mltc/chat/${data.room_information.room_id}/"]`);

        if (existingAnchor) {
            existingAnchor.parentNode.removeChild(existingAnchor);
        }

        let user_data = `
        <a href="/mltc/chat/${data.room_information.room_id}/">
         <div class="sidebar_info d-flex active-bg">
           <div class="user_info_image">
              <img src="${data.image_url}" alt="user_img" class="img-fluid">
           </div>
           <div class="user_data">
              <h5>
              ${data.sender_name}
              </h5>
           
              ${data.room_information.message_type === "text" ?
                '<p><strong>' + data.room_information.last_message + '</strong></p>' :
                data.room_information.message_type === "image" ?
                '<p><strong>sent as an image</strong></p>' :
                data.room_information.message_type === "video" ?
                '<p><strong>sent as a video</strong></p>' :
                data.room_information.message_type === "file" ?
                '<p><strong>sent as a file</strong></p>':
                data.room_information.message_type === "audio" ?
                '<p><strong>sent as a audio</strong></p>' :
                '<p><strong>unknown message type</strong></p>'} 
           </div>
           <div class="chat_data_right">
           <div class="chat_dropdown">
            <span class="badge rounded-pill text-bg-success">${data.room_information.mltc_room_unread_count }</span>
               <div class="dropdown text-end position-relative d-flex justify-content-end align-items-center gap-3 mb-2">
                   <span class="pin_convo"  style="display:none"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#000" class="bi bi-pin-fill" viewBox="0 0 16 16">
                       <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354"/>
                     </svg></span>
                   <button class="d-flex btn dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                       <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-three-dots-vertical" viewBox="0 0 16 16">
                           <path d="M9.5 13a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"></path>
                       </svg>
                   </button>
                   <ul class="dropdown-menu">
                   <li class="pinconversation" onclick="pin_conversation('${data.room_information.room_id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pin" viewBox="0 0 16 16">
                   <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354m1.58 1.408-.002-.001zm-.002-.001.002.001A.5.5 0 0 1 6 2v5a.5.5 0 0 1-.276.447h-.002l-.012.007-.054.03a5 5 0 0 0-.827.58c-.318.278-.585.596-.725.936h7.792c-.14-.34-.407-.658-.725-.936a5 5 0 0 0-.881-.61l-.012-.006h-.002A.5.5 0 0 1 10 7V2a.5.5 0 0 1 .295-.458 1.8 1.8 0 0 0 .351-.271c.08-.08.155-.17.214-.271H5.14q.091.15.214.271a1.8 1.8 0 0 0 .37.282"/>
                    </svg></span>Pin Conversation</li>
                    <li onclick="mark_conversation('${data.room_information.room_id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chat-left" viewBox="0 0 16 16">
                        <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
                        </svg></span> Mark as My Conversation</li>
                    <li onclick="close_conversation('${data.room_information.room_id}')><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-circle" viewBox="0 0 16 16">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
                        <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708"/>
                        </svg></span> Close Conversation</li>
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
     </a>
     `

     mltc_sidebar = document.querySelector("#mltc_sidebar")  
     targetDiv = mltc_sidebar.querySelector('.active_chats');
     targetDiv.insertAdjacentHTML('afterbegin', user_data); 
    }
    if (data.room_information.room_type === 'np') {
        const np_countBadge = document.getElementById('np_count_badge');
        if (np_countBadge) {
            const currentCount = parseInt(np_countBadge.textContent, 10) || 0;
            np_countBadge.textContent = currentCount + 1;
        }
        let li_data = `<li>
        <button onclick="np_notification('${data.room_information.room_id}')">
        ${data.sender_name} ${data.message}
        </button>
        </li>`
        document.getElementById("np_notification_inner").innerHTML = li_data;
   

        const existingAnchor = document.querySelector(`a[href="/np/chat/${data.room_information.room_id}/"]`);

        if (existingAnchor) {
            existingAnchor.parentNode.removeChild(existingAnchor);
        }

        let user_data = `
        <a href="/np/chat/${data.room_information.room_id}/">
         <div class="sidebar_info d-flex active-bg">
           <div class="user_info_image">
              <img src="${data.image_url}" alt="user_img" class="img-fluid">
           </div>
           <div class="user_data">
              <h5>
              ${data.sender_name}
              </h5>
           
              ${data.room_information.message_type === "text" ?
                '<p><strong>' + data.room_information.last_message + '</strong></p>' :
                data.room_information.message_type === "image" ?
                '<p><strong>sent as an image</strong></p>' :
                data.room_information.message_type === "video" ?
                '<p><strong>sent as a video</strong></p>' :
                data.room_information.message_type === "file" ?
                '<p><strong>sent as a file</strong></p>':
                data.room_information.message_type === "audio" ?
                '<p><strong>sent as a audio</strong></p>' :
                '<p><strong>unknown message type</strong></p>'} 
           </div>
          <div class="chat_data_right">
                                                    <div class="chat_dropdown">
                                                    <span class="badge rounded-pill text-bg-success">${data.room_information.hha_room_unread_count } </span>
                                                        <div class="dropdown text-end position-relative d-flex justify-content-end align-items-center gap-3 mb-2">
                                                            <span class="pin_convo"  style="display:none"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#000" class="bi bi-pin-fill" viewBox="0 0 16 16">
                                                                <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354"/>
                                                              </svg></span>
                                                            <button class="d-flex btn dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-three-dots-vertical" viewBox="0 0 16 16">
                                                                    <path d="M9.5 13a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0"></path>
                                                                </svg>
                                                            </button>
                                                            <ul class="dropdown-menu">
                                                                 <li class="pinconversation" onclick="pin_conversation('${data.room_information.room_id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pin" viewBox="0 0 16 16">
                                                                        <path d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354m1.58 1.408-.002-.001zm-.002-.001.002.001A.5.5 0 0 1 6 2v5a.5.5 0 0 1-.276.447h-.002l-.012.007-.054.03a5 5 0 0 0-.827.58c-.318.278-.585.596-.725.936h7.792c-.14-.34-.407-.658-.725-.936a5 5 0 0 0-.881-.61l-.012-.006h-.002A.5.5 0 0 1 10 7V2a.5.5 0 0 1 .295-.458 1.8 1.8 0 0 0 .351-.271c.08-.08.155-.17.214-.271H5.14q.091.15.214.271a1.8 1.8 0 0 0 .37.282"/>
                                                                      </svg></span>Pin Conversation</li>
                                                                <li onclick="mark_conversation('${data.room_information.room_id}')"><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chat-left" viewBox="0 0 16 16">
                                                                    <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
                                                                  </svg></span> Mark as My Conversation</li>
                                                                <li onclick="close_conversation('${data.room_information.room_id}')><span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-circle" viewBox="0 0 16 16">
                                                                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
                                                                    <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708"/>
                                                                  </svg></span> Close Conversation</li>
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
     </a>
     </div>`
        np_sidebar = document.querySelector("#np_sidebar")  
        targetDiv = np_sidebar.querySelector('.active_chats');
        targetDiv.insertAdjacentHTML('afterbegin', user_data);
    }

    
}
function hha_notification(roomId) {

    $.ajax({
        type: 'GET',
        url: '{% url "notification" %}',  
        data: {
            chatroomId: roomId
        },
        success: function(response) {
            window.location.href = window.location.origin + '/hha/chat/' + roomId;

        },
        error: function(error) {
            console.error('Error marking notification as seen:', error);
        }
    });

 
}

function mltc_notification(roomId) {
    $.ajax({
        type: 'GET',
        url: '{% url "notification" %}',  
        data: {
            chatroomId: roomId
        },
        success: function(response) {
            window.location.href = window.location.origin + '/mltc/chat/' + roomId;

        },
        error: function(error) {
            console.error('Error marking notification as seen:', error);
        }
    });

 
}

function np_notification(roomId) {

    $.ajax({
        type: 'GET',
        url: '{% url "notification" %}',  
        data: {
            chatroomId: roomId
        },
        success: function(response) {
            window.location.href = window.location.origin + '/np/chat/' + roomId;

        },
        error: function(error) {
            console.error('Error marking notification as seen:', error);
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
