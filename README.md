# otto-hzys-py-tool
## 实现方式
借用[电棍otto语音活字印刷生成](https://github.com/HanaYabuki/otto-hzys)的纯前端，编写的API服务，支持高并发（由于使用无头浏览器，对cpu要求较高）
## 如何部署
### 安装服务核心并PATCH
1. https://github.com/HanaYabuki/otto-hzys
2. 修改`otto-hzys/src/components/OttoHzys.vue`的`downloadSound`函数
    ```diff
    -//crunker.download(audioSrc.blob, audioSrc.name);
    +window.ottoVoice=audioSrc.value;
    ```
3. `npm i`
4. `npm run serve`

### 安装依赖
`pdm install`

`pdm venv activate`
## 运行
`python3 -m otto_hzys_py_tool`
## 使用方式
见 **/otto-hzys-py-tool/tests/\_\_main\_\_.py**