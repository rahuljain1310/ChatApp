import React from 'react';
import socketIOClient from "socket.io-client";

const socket = socketIOClient('http://localhost:5000');

export default class VideoPane extends React.Component {
  constructor(props) {
    super(props)
    window.onbeforeunload = this.sendMessage('bye')
    this.state = {
      // response: 0,
      // endpoint: "http://localhost:5000",
      isChannelReady: false,
      isInitiator: false,
      isStarted: false,
      localStream: null,
      pc: null,
      remoteStream: null,
      turnReady: null,
      pcConfig: { 'iceServers': [{ 'urls': 'stun:stun.l.google.com:19302' }] },
      sdpConstraints: {
        offerToReceiveAudio: true,
        offerToReceiveVideo: true
      },
      constraints: {video: true},
    }
  }

  stop = () => {
    this.state.pc.close();
    this.setState({isStarted: false,pc: null})
  }
  handleRemoteHangup = () => {
  console.log('Session terminated.')
  this.stop()
  this.setState({isInitiator: false})
  }
  hangup = () => {
    console.log('Hanging up.');
    this.hangupButton.disabled = true;
    this.stop();
    this.sendMessage('bye');
  }
 
  sendMessage = (message) => {
    console.log('Client sending message: ', message);
    socket.emit('message', message);
  }

  
  maybeStart = () => {
    let { isStarted, localStream, isChannelReady, isInitiator} = this.state
    console.log('>>>>>>> maybeStart() ', isStarted, localStream, isChannelReady);
    if (!isStarted && typeof localStream !== 'undefined' && isChannelReady) {
      console.log('>>>>>> creating peer connection');
      this.createPeerConnection();
      this.state.pc.addStream(localStream);
      this.setState({isStarted: true});
      console.log('isInitiator', isInitiator);
      if (isInitiator) {
        this.doCall();
      }
    }
  }

  gotStream = (stream) => {
    console.log('Adding local stream.')
    this.setState({localStream: stream})
    this.localVideo.srcObject = stream
    this.sendMessage('got user media')
    if (this.state.isInitiator) {
      this.maybeStart();
    }
  }

  startLocalStream = () => {
    console.log('Requesting local stream');
    this.startButton.disabled = true;
    navigator.mediaDevices.getUserMedia({
      audio: true,
      video: true
    }).then(this.gotStream).catch(function(e) {
      alert('getUserMedia() error: ' + e.name);
    });
    console.log('Getting user media with constraints', {video: true});
  }

  // Handling RTC Peer Connection 
  
  handleIceCandidate = (event) => {
    console.log('icecandidate event: ', event);
    if (event.candidate) {
      this.sendMessage({
        type: 'candidate',
        label: event.candidate.sdpMLineIndex,
        id: event.candidate.sdpMid,
        candidate: event.candidate.candidate
      });
    } else {
      console.log('End of candidates.');
    }
  }
  handleRemoteStreamRemoved = (event) => {
    console.log('Remote stream removed. Event: ', event);
  }  
  handleRemoteStreamAdded = (event) => {
    console.log('Remote stream added.');
    this.setState({remoteStream: event.stream})
    this.remoteVideo.srcObject = event.stream
  }

  createPeerConnection = () => {
    try {
      let x = new RTCPeerConnection(null);
      x.onicecandidate = this.handleIceCandidate;
      x.onaddstream = this.handleRemoteStreamAdded;
      x.onremovestream = this.handleRemoteStreamRemoved;
      this.setState({pc: x})
      console.log('Created RTCPeerConnnection');
    } catch (e) {
      console.log('Failed to create PeerConnection, exception: ' + e.message);
      alert('Cannot create RTCPeerConnection object.');
      return;
    }
  }


  // Sending/Receiving Offer to Peer

  onCreateSessionDescriptionError = (error) => console.trace('Failed to create session description: ' + error.toString())
  handleCreateOfferError = (event) => console.log('createOffer() error: ', event)
  setLocalAndSendMessage = (sessionDescription) => {
    this.state.pc.setLocalDescription(sessionDescription);
    console.log('setLocalAndSendMessage sending message', sessionDescription);
    this.sendMessage(sessionDescription);
  }
  doCall = () => {
    console.log('Sending offer to peer');
    this.state.pc.createOffer(this.setLocalAndSendMessage, this.handleCreateOfferError);
  }
  
  doAnswer = () => {
    console.log('Sending answer to peer.');
    this.state.pc.createAnswer().then(this.setLocalAndSendMessage,this.onCreateSessionDescriptionError)
  }


  requestTurn = (turnURL) => {
    let {pcConfig,turnReady} = this.state
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
  

  componentDidMount() {
    // const { endpoint } = this.state;
    this.startLocalStream()

    let room = prompt('Enter room name:');
    if (room !== '') {
      socket.emit('create or join', room);
      console.log('Attempted to create or  join room', room);
    }
    let {isInitiator,isStarted} = this.state
    socket.on('created', (room) => {
      console.log('Created room ' + room)
      this.setState({isInitiator: true})
    });
    socket.on('full', (room) => console.log('Room ' + room + ' is full'));
    socket.on('log', (array) => console.log.apply(console, array));
    socket.on('join', (room) => {
      console.log('Another peer made a request to join room ' + room);
      console.log('This peer is the initiator of room ' + room + '!');
      this.setState({isChannelReady: true})
    });
    socket.on('joined', (room) => {
      console.log('joined: ' + room)
      this.setState({isChannelReady: true})
    });
    socket.on('message', (message) => {
      console.log('Client received message:', message);
      if (message === 'got user media') {
        this.maybeStart();
      } else if (message.type === 'offer') {
        if (!isInitiator && !isStarted) {
          this.maybeStart();
        }
        this.state.pc.setRemoteDescription(new RTCSessionDescription(message));
        this.doAnswer();
      } else if (message.type === 'answer' && isStarted) {
        this.state.pc.setRemoteDescription(new RTCSessionDescription(message));
      } else if (message.type === 'candidate' && isStarted) {
        var candidate = new RTCIceCandidate({
          sdpMLineIndex: message.label,
          candidate: message.candidate
        });
        this.state.pc.addIceCandidate(candidate);
      } else if (message === 'bye' && isStarted) {
        this.handleRemoteHangup();
      }
    });

    if (window.location.hostname !== 'localhost') {
      this.requestTurn('https://computeengineondemand.appspot.com/turn?username=41784574&key=4080218913');
    }
  }

  render() {
    return (
      <div>
        <div id="videos">
          <video id="localVideo" autoPlay muted playsInline ref={video => (this.localVideo = video)}></video>
          <video id="remoteVideo" autoPlay playsInline ref={video => (this.remoteVideo = video)}></video>
          <div>
            <button id="startButton" ref={button=>(this.startButton=button)}>Start</button>
            <button id="callButton" ref={button=>(this.callButton=button)}>Call</button>
            <button id="hangupButton" ref={button=>(this.hangupButton=button)}>Hang Up</button>
            <button id="logout">Logout</button>
          </div>
        </div>
      </div>
    );
  }
}
