import axios from "axios"


export function streamAnalyze(data, onMessage) {

  const xhr = new XMLHttpRequest()

  xhr.open("POST", "http://127.0.0.1:8080/api/v1/stream-analyze")

  xhr.setRequestHeader("Content-Type", "application/json")

  xhr.onprogress = function () {

    const response = xhr.responseText

    onMessage(response)
  }

  xhr.send(JSON.stringify(data))
}