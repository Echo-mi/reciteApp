//app.js
App({
  onLaunch: function () {
    // 展示本地存储能力
    let logs = wx.getStorageSync('logs') || []
    let app_this = this
    logs.unshift(Date.now())
    wx.setStorageSync('logs', logs)
  },

  globalData: {
    userInfo: null,
    host: "http://10.161.223.10:8000/ebrose/",
    cookie: "",
    pivot: ""
  }
})
