var vm = new Vue({
    el:"#app",
    data:{
        host:host,
        username:'',
        password:'',
        error_username :false,
        error_pwd : false,
        error_username_message :'输入错误',
        error_pwd_message:'输入错误',
        remember:false
    },
    methods:{
       // 获取url路径?号后面的name值的参数
        // http://www.jd.com/login.html?a=200&next=www.boxuegu.com&b=200
        get_query_str:function (name) {
            var reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)', 'i');
            var r = window.location.search.substr(1).match(reg);
            if (r != null){
                return decodeURI(r[2]);
            }
            return null
        },
        //检查用户名
        check_username:function () {
            if(!this.username){
                this.error_username = true;
                this.error_username_message = '请填写用户名';
            }else {
                this.error_username = false;
            }
        },
        check_pwd:function () {
             if(!this.password){
                this.error_pwd = true;
                this.error_pwd_message = '请填写用户名';
            }else {
                this.error_pwd = false;
            }
        },
        //表单提交
        on_submit:function () {
            this.check_username();
            this.check_pwd();
            if(this.error_pwd == false && this.error_username == false){
                axios.post(this.host +'/authorizations/',{
                    'username':this.username,
                    'password':this.password
                },{
                    responseType:'json',
                    //允许携带cookie
                     withCredentials: true
                }).then(response => {
                    //登陆成功，装填保持
                    //记住密码
                    if(this.remember){

                        sessionStorage.clear();
                        localStorage.token = response.data.token;
                        localStorage.username = response.data.username;
                        localStorage.user_id = response.data.user_id
                    }
                    else {
                        //未记住密码
                        localStorage.clear();
                        sessionStorage.token = response.data.token;
                        sessionStorage.username = response.data.username;
                        sessionStorage.user_id = response.data.user_id

                    }
                    //登陆成功后跳转页面
                    var return_url = this.get_query_str('next');
                    if(!return_url){
                        return_url = '/index.html';
                    }
                    location.href = return_url


                }).catch(error => {
                    this.error_pwd_message = '用户名或者密码错误';
                    this.error_pwd = true;
                })
            }
        },
        qq_login:function () {
            var state = this.get_query_str('next') || '/';
            axios.get(this.host +"/oauth/qq/authorization/?state=" + state,
                {responseType:'json'}).then(response => {
                location.href = response.data.auth_url;
            }).catch(error => {
                console.log(error.response.data)
            })
        }
    }
});