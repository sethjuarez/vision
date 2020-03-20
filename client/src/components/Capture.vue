<template>
    <div>
        <div id="instructions">
            <p><strong>Capture Instructions</strong></p>
            <ol>
                <li>Select desired gesture</li>
                <li>Get into position!</li>
                <li>Spacebar to start</li>
            </ol>
            <p><strong>Training Instructions</strong></p>
            <p>Once you uploaded a balanced set of pictures for each category
                head over to <a href="https://customvision.ai">customvision</a> to train and download the model</p>
        </div>
        <div id="radioselection">
            <span :key="item+index" v-for="(item, index) in labels">
                <input type="radio" :id="item" name="sign" :value="item" 
                    :checked="selectedSign == item"
                    v-model="selectedSign">
                <label :for="item">{{item}}</label>
                &nbsp;
            </span>
            <div v-if="interval != null">Click Spacebar to Stop!</div>
        </div>
        <div id="images">
            <div id="videoPane">
                <video id="video" width="320" height="240" autoplay></video>
                <div id="deviceOptions">
                    <select name="deviceSelection" @input="setDevice">
                        <option :key="idx" v-for="(ditem, idx) in devices" value="ditem.deviceId">{{ditem.label}}</option>
                    </select>
                </div>
                <canvas id="rendered" width="224" height="224"></canvas>
                <canvas id="canvas" width="320" height="240"></canvas>
            </div>
            <div id="output">
                <div id="flavor" v-if="modelmeta != null">Type: {{modelmeta.Flavor}}</div>
                <div id="exported" v-if="modelmeta != null">Exported: {{modelmeta.ExportedDate}}</div>
                <div id="current">{{guess}}</div>
                <div id="plist">
                    <ul>
                        <li :key="idx" v-for="(pitem, idx) in probabilities">{{pitem.label}}: {{pitem.probability.toFixed(2)}}%</li>
                    </ul>
                </div>
            </div>
        </div>
        <div id="listOPics" v-if="list.length > 0">
            <div>Click on an image to remove (or <button type="button" v-on:click="clearImages()">Clear All</button>)</div>
            <div>(Also maybe clean out any images that might be ambiguous if possible)</div>
            <div id="warning" v-if="list.length >= 64">64 Limit Reached - either submit or remove some images</div>
            <ul class="imagelist" :key="index" v-for="(item, index) in list">
                <li class="imgitem" @click="removeImage(index)">
                    <div>{{item.type}}</div>
                    <img height="120" width="160" :src="item.image" />
                </li>
            </ul>
            <div class="btn">
                <button type="button" v-if="list.length > 0" v-on:click="submitImages()" v-show="!processing">Submit Training Data</button>
            </div>
        </div>
        <div id="notifications" v-show="processing" v-on:click="processing=!processing"> 
            {{message}}
        </div>
    </div>
</template>

<script>
    import axios from 'axios'
    import * as cvstfjs from 'customvision-tfjs'

    export default {
        name: 'Capture',
        data: function () {
            return {
                processing: false,
                message: '',
                video: null,
                canvas: null,
                selectedSign: 'none',
                list: [],
                lastresponse: null,
                interval: null,
                model: null,
                modelmeta: null,
                labels: ['none', 'Bit', 'Doug', 'Penny'],
                modelLabels: [],
                probabilities: [],
                guess: 'none',
                vdim: {
                    'width': 0,
                    'height': 0
                },
                appSettings: '',
                devices: []
            }
        },
        mounted: async function () {
            // map spacebar key event
            document.onkeyup = this.key

            // get canvas context
            let canvas = document.getElementById('canvas')
            this.canvas = canvas.getContext('2d')

            // enumerate video devices
            if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                const items = await navigator.mediaDevices.enumerateDevices();
                this.devices = items.filter(device => device.kind === 'videoinput');
            }

            // get video reference
            this.video = document.getElementById('video')
            

            // load appSettings
            let response = await axios.get('config.json')
            this.appSettings = response.data
            console.log(this.appSettings)

            // load model
            await this.loadModel()
            
        },
        methods: {
            setDevice: async function(value) {
                const device = this.devices[value.target.selectedOptions[0].index]
                
                if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    let stream = await navigator.mediaDevices.getUserMedia({
                        video: {
                            deviceId: {
                                exact: device.deviceId
                            }
                        }
                    })
                    let tracks = stream.getVideoTracks()
                    if(tracks.length >= 1) {
                        let settings = tracks[0].getSettings()
                        this.vdim.width = settings.width
                        this.vdim.height = settings.height
                        this.video.srcObject = stream
                        this.video.play()
                    }
                }
                console.log(device)
            },
            loadModel: async function() {
                // load model
                this.model = new cvstfjs.ClassificationModel()
                try {
                    await this.model.loadModelAsync('model/model.json')

                    // load metadata and labels
                    let manifest = await axios.get('model/cvexport.manifest')
                    this.modelmeta = manifest.data
                    let l = await axios.get('model/labels.txt')
                    this.modelLabels = l.data.split('\n').map(e => {
                        return e.trim()
                    })
                    
                    // start prediction interval
                    setInterval(this.predict, 1000)
                } catch (error) {
                    this.guess = 'model error'
                    console.log(error)
                }
            },
            predict: async function () {
                // draw video image on canvas
                var pic = document.getElementById('rendered')
                var ctx = pic.getContext('2d')
                ctx.drawImage(this.video, 0, 0, 320, 240)

                // run prediction
                const prediction = await this.model.executeAsync(pic)
                let pred = prediction[0]

                // get label and populate probabilities
                this.guess = this.modelLabels[pred.indexOf(Math.max(...pred))]
                this.probabilities = pred.map((e, i) => { 
                    return { 'label': this.modelLabels[i], 'probability': e*100 }
                })
            },
            key: function (event) {
                if(event.keyCode == 32) {
                    if(this.interval != null)
                        this.stopCapture()
                    else
                        this.startCapture()
                }
            },
            startCapture: function () {
                this.stopCapture()
                setTimeout(this.stopCapture, 60010)
                this.interval = setInterval(this.addImage, 500)
                this.video.style.border = "thick solid #FF0000"
            },
            stopCapture: function () {
                if(this.interval != null) {
                    clearInterval(this.interval);
                    this.interval = null;
                    this.video.style.border = "solid 1px gray"
                }
            },
            addImage: function () {
                if(this.list.length <  64) {
                    this.canvas.drawImage(this.video, 0, 0, 320, 240)
                    let c = document.getElementById('canvas')
                    this.list.push({
                        type: this.selectedSign,
                        image: c.toDataURL()
                    })
                } else {
                    // reached max
                    this.stopCapture()
                }
            },
            removeImage: function (index) {
                this.list.splice(index, 1)
            },
            clearImages: function () {
                this.list = []
                this.processing = false
            },
            submitImages: async function () {
                this.processing = true
                this.message = 'sending data'
                // api endpoint
                try {
                    let url = this.appSettings.saveEndpoint
                    let max_submit = this.appSettings.maxSubmitCount

                    for(let i = 0; i < this.list.length; i+=max_submit) {
                        let response = await axios.post(url, { items: this.list.slice(i, i+max_submit) }, {
                            headers: { 'Content-Type': 'application/json' }
                        })
                        this.lastresponse = response['data']
                    }
                    
                    this.message = 'done!'
                    this.list = []
                    this.processing = false
                } catch(error) {
                    // uh oh - log error and reset
                    console.log(error)
                    this.processing = false
                }
            }
        }
    }
</script>

<style scoped>
    #instructions {
        width: 640px;
        margin: 0px auto;
        text-align: left;
    }
    video {
        border: solid 1px gray;
        transform: rotateY(180deg);
        -webkit-transform:rotateY(180deg); /* Safari and Chrome */
        -moz-transform:rotateY(180deg); /* Firefox */
        float: left;
    }

    #output {
        border: solid 1px gray;
        height: 240px;
        width: 320px;
        margin-left: 10px;
        float: right;
        clear: right;
        text-align: left;
        padding: 0px 4px;
    }

    #videoPane {
        float: left;
        height: 275px;
    }

    #deviceOptions {
        margin-top: 20px;
        padding: 10px;
    }

    #images{
        margin: 0px auto;
        width: 700px;
        /* border: solid 10px red;*/
    }

    #rendered {
        display: none;
    }

    #canvas {
        display: none;
    }
    #warning {
        color: red;
        font-size: 16px;
        font-weight: bold;
    }
    #listOPics {
        clear: both;
        padding: 25px 100px;
        text-align: center;
        margin: 0px;
    }
    #radioselection {
        margin-bottom: 10px;
    }

    #notifications {
        width:150px;
        height:30px;
        display:table-cell;
        text-align:center;
        background:rgb(255, 166, 0);
        border:1px solid #000;
        bottom: 10px;
        right: 10px;
        position: absolute;
        padding-top: 10px;
    }

    .imagelist {
        list-style-type: none;
        padding: 0px;
    }

    .imgitem {
        float: left;
        padding: 10px;
    }

    .btn {
        text-align: center;
        clear: both;
    }
    #plist ul {
        margin: 1px;
    }
    #plist li {
        /*border: solid 1px black;*/
        margin: 5px;
    }

    #current {
        text-align: center;
        margin: 3px;
        font-size: 30px;
        color: red;
        font-weight: bolder;
    }

    #flavor {
        margin-top: 5px;
        margin-bottom: 5px;
    }

    #exported {
        margin-bottom: 5px;
    }
    #console {
        margin: 20px;
    }
</style>
