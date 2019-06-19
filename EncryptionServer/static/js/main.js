'use strict';

var isChannelReady = false;
var isInitiator = false;
var isStarted = false;
var localStream;
var pc;
var pc_array = [null, null, null, null, null];
var remoteStream;
var turnReady;
var roomid = -1;
var totalClient = 0;
var PeerId;
var PeerToAnswer;

var pcConfig = {
  'iceServers': [{
    'urls': 'stun:stun.l.google.com:19302'
  }]
};

// Set up audio and video regardless of what devices are present.
var sdpConstraints = {
  offerToReceiveAudio: true,
  offerToReceiveVideo: true
};

///////////////////////////////////////////////

var localVideo = document.querySelector('#localVideo');
var remoteVideo;

///////////////////////////////////////////////

var socket = io.connect();

var room;
room = prompt('Enter room name:');
if (room !== '') {
  socket.emit('create or join', room);
  console.log('Attempted to create or  join room', room);
}

///////////////////////////////////////////////

socket.on('created', function(room) {
  console.log('Created room ' + room);
  isInitiator = true,
  totalClient = 1;
  roomid = 1;
});

socket.on('full', function(room) {
  console.log('Room ' + room + ' is full');
});

socket.on('join', function (room) {
  console.log('Another peer made a request to join room ' + room.room);
  console.log('This peer is the initiator of room ' + room.room + '!');
  remoteVideo = document.querySelector('#remoteVideo'+(room.numClients-1));
  isChannelReady = true;
  isInitiator = false;
  pc = null;
});

socket.on('joined', function(dict) {
  if(roomid === -1) {
    isInitiator = true
    roomid = dict.roomid;
    remoteVideo = document.querySelector('#remoteVideo1');
  }
  totalClient = dict.numClients
  PeerToAnswer = totalClient
  console.log("Roomid: "+dict.roomid+' joined: ' + dict.room+",Total Clients: "+totalClient);
  isChannelReady = true;
  isStarted = false;
  pc = null;
});

socket.on('log', function(array) {
  console.log(array);
});

////////////////////////////////////////////////

function sendMessage(message) {
  console.log('Client sending message: ', message);
  if(typeof message === 'object') message['sendBy'] = roomid.toString()
  socket.emit('message', message);
}

socket.on('message', function(message) {
  console.log('Client received message:', message);
  if (message === 'got user media') {
    maybeStart();
  } else if (message.type === 'offer') {
    if (message.sendTo===roomid.toString()) {
      if(!isInitiator && !isStarted ) maybeStart();
      pc.setRemoteDescription(new RTCSessionDescription(message));
      let answer_to = parseInt(message.sendBy)
      pc_array[answer_to] = pc
      doAnswer(answer_to);
    }
  } else if (message.type === 'answer' && isStarted && PeerToAnswer===roomid) {
    pc_array[message.sendBy].setRemoteDescription(new RTCSessionDescription(message));
  } else if (message.type === 'candidate' && isStarted) {
    var candidate = new RTCIceCandidate({
      sdpMLineIndex: message.label,
      candidate: message.candidate
    });
    let x = parseInt(message.sendBy)
    pc_array[x].addIceCandidate(candidate);
  } else if (message === 'bye' && isStarted) {
    handleRemoteHangup();
  }
});

////////////////////////////////////////////////////


navigator.mediaDevices.getUserMedia({
  audio: false,
  video: true
}).then(gotStream).catch(function(e) {
  alert('getUserMedia() error: ' + e.name);
});

function gotStream(stream) {
  console.log('Getting user media with constraints',  {video: true});
  console.log('Adding local stream.');
  localStream = stream;
  console.log(stream)
  localVideo.srcObject = stream;
  sendMessage('got user media');
  if (isInitiator) maybeStart();
}

/////////////////////////////////////////////////////
if (location.hostname !== 'localhost') {
  requestTurn(
    'https://computeengineondemand.appspot.com/turn?username=41784574&key=4080218913'
  );
}
function requestTurn(turnURL) {
  var turnExists = false;
  for (var i in pcConfig.iceServers) {
    if (pcConfig.iceServers[i].urls.substr(0, 5) === 'turn:') {
      turnExists = true;
      turnReady = true;
      break;
    }
  }
  if (!turnExists) {
    console.log('Getting TURN server from ', turnURL);
    // No TURN server. Get one from computeengineondemand.appspot.com:
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200) {
        var turnServer = JSON.parse(xhr.responseText);
        console.log('Got TURN server: ', turnServer);
        pcConfig.iceServers.push({
          'urls': 'turn:' + turnServer.username + '@' + turnServer.turn,
          'credential': turnServer.password
        });
        turnReady = true;
      }
    };
    xhr.open('GET', turnURL, true);
    xhr.send();
  }
}
window.onbeforeunload = function() {
  sendMessage('bye');
};
/////////////////////////////////////////////////////

function maybeStart() {
  console.log('>>>>>>> maybeStart() ', isStarted, localStream, isChannelReady);
  if (!isStarted && typeof localStream !== 'undefined' && isChannelReady) {
    if(PeerToAnswer===roomid) {
      for(let i=1;i<totalClient;i++) {
        setTimeout(function() {
          pc_array[i] = createPeerConnection(localStream);
          isStarted = true;
          console.log('isInitiator', isInitiator);
          remoteVideo =  document.querySelector('#remoteVideo'+i);
          if (isInitiator) doCall(i);
        },3000*(i-1))
      }
    } else {
      pc = createPeerConnection(localStream)
      isStarted = true
    }
  }
}

/////////////////////////////////////////////////////////

function createPeerConnection() {
  try {
    console.log('>>>>>> creating peer connection');
    pc = new RTCPeerConnection(null);
    pc.onicecandidate = handleIceCandidate;
    pc.onaddstream = handleRemoteStreamAdded;
    pc.onremovestream = handleRemoteStreamRemoved;
    pc.addStream(localStream);
    console.log('Created RTCPeerConnnection');
    return pc;
  } catch (e) {
    console.log('Failed to create PeerConnection, exception: ' + e.message);
    alert('Cannot create RTCPeerConnection object.');
    return;
  }
}

function handleIceCandidate(event) {
  console.log('icecandidate event: ', event);
  if (event.candidate) {
    sendMessage({
      type: 'candidate',
      label: event.candidate.sdpMLineIndex,
      id: event.candidate.sdpMid,
      candidate: event.candidate.candidate,
    });
  } else {
    console.log('End of candidates.');
  }
}

function handleCreateOfferError(event) {
  console.log('createOffer() error: ', event);
}

function doCall(i) {
  PeerId = i
  console.log('Sending offer to peer');
  pc_array[i].createOffer(setLocalAndSendMessage, handleCreateOfferError);
}

function doAnswer(i) {
  console.log('Sending answer to peer.');
  PeerId = i
  pc_array[PeerId].createAnswer().then(
    setLocalAndSendMessage,
    onCreateSessionDescriptionError
  );
}

function setLocalAndSendMessage(sessionDescription) {
  pc_array[PeerId].setLocalDescription(sessionDescription);
  console.log(PeerId)
  let ObjectSD = {
    type: sessionDescription.type,
    sdp: sessionDescription.sdp,
    sendTo: PeerId.toString()
  }
  console.log('setLocalAndSendMessage sending message', ObjectSD);
  sendMessage(ObjectSD);
}

function onCreateSessionDescriptionError(error) {
  console.log('Failed to create session description: ' + error.toString());
}

function handleRemoteStreamAdded(event) {
  console.log('Remote stream added.');
  remoteStream = event.stream;
  remoteVideo.srcObject = remoteStream;
}

function handleRemoteStreamRemoved(event) {
  console.log('Remote stream removed. Event: ', event);
}

function hangup() {
  console.log('Hanging up.');
  stop();
  sendMessage('bye');
}

function handleRemoteHangup() {
  console.log('Session terminated.');
  stop();
  isInitiator = false;
}

function stop() {
  isStarted = false;
  pc.close();
  pc = null;
}
