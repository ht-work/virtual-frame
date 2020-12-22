package web

import (
	"encoding/json"
	"errors"
	"github.com/dgrijalva/jwt-go"
	"github.com/gin-gonic/gin"
	"iaas/model"
	"iaas/pkgs/database"
	"io/ioutil"
	"net/http"
	"time"
)

const (
	inner_token = "chinamobileiaaschinamobileiaas"
	// 盐
	Secret     = "瞅你咋地？"
	ExpireTime = 3600
)

//type Response struct {
//	Code int    `json:"code"`
//	Msg  string `json:"msg,omitempty"`
//	Err  error  `json:"err_msg,omitempty"`
//}

// 定义claim包含的内容
type jwtClaims struct {
	jwt.StandardClaims
	UserID   uint   `json:"user_id"`
	UserName string `json:"user_name"`
	Password string `json:"Password"`
}

func (p *App) Login(c *gin.Context) {
	var user model.User

	param := make(map[string]map[string]string)
	//param["params"] = make(map[string]interface{})

	data, _ := ioutil.ReadAll(c.Request.Body)
	log.Info(string(data))
	_ = json.Unmarshal(data, &param)

	user.Name = param["params"]["username"]
	user.Passwd = param["params"]["password"]
	if user.Name == "" || user.Passwd == "" {
		c.JSON(http.StatusBadRequest, ParameterError(""))
		c.Abort()
		return
	}

	//先判断用户是否存在，存在再判断密码是否正确
	Bool := validUser(&user)

	if Bool {
		claims := &jwtClaims{
			UserName: user.Name,
			Password: user.Passwd,
		}
		claims.IssuedAt = time.Now().Unix()
		claims.ExpiresAt = time.Now().Add(time.Minute * time.Duration(ExpireTime)).Unix()
		signedToken, err := getToken(claims)
		if err != nil {
			c.JSON(http.StatusBadRequest, UnknownError("create token failed"))
			c.Abort()
			return
		}
		log.Info(claims.UserName)
		c.JSON(http.StatusOK, gin.H{
			"code":     0,
			"username": user.Name,
			"token":    signedToken,
		})
	} else {
		c.JSON(http.StatusUnauthorized, UnauthorizedError("user not exist or invalid password"))
		c.Abort()
		return
	}
}

func (p *App) ChangePasswd(c *gin.Context) {
	var user model.User

	param := make(map[string]map[string]string)
	//param["params"] = make(map[string]interface{})

	data, _ := ioutil.ReadAll(c.Request.Body)
	//log.Info(string(data))
	_ = json.Unmarshal(data, &param)

	username := param["params"]["username"]
	password := param["params"]["password"]
	newPw := param["params"]["newPassword"]
	if username == "" || password == "" || newPw == "" {
		c.JSON(http.StatusBadRequest, ParameterError("err param"))
		c.Abort()
		return
	}

	//先判断用户是否存在，存在再判断密码是否正确
	user.Name = username
	user.Passwd = password
	Bool := validUser(&user)

	if !Bool {
		c.JSON(http.StatusUnauthorized, UnauthorizedError("user not exist or invalid password"))
		c.Abort()
		return
	}

	e := database.DBConn.Conn.Model(user).Updates(&model.User{Name: username,Passwd: newPw}).Error

	if e != nil {
		c.JSON(http.StatusBadRequest, UnknownError("change password failed"))
		c.Abort()
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":     0,
		"username": user.Name,
	})
}

func MiddleWareAuth() gin.HandlerFunc {
	//res := &APIException{}
	return func(c *gin.Context) {
		cliToken := c.Request.Header.Get("token")

		if cliToken == "" {
			log.Errorln("not found token in request")
			c.JSON(http.StatusUnauthorized, ParameterError("unauthorized, token not found"))
			c.Abort()
			return
		}

		_, err := verifyToken(cliToken)
		if err != nil {
			c.JSON(http.StatusUnauthorized, UnauthorizedError("Unauthorized, invalid token"))
			c.Abort()
			return
		}
		c.Next()
	}
}

func getToken(claims *jwtClaims) (string, error) {
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signedToken, err := token.SignedString([]byte(Secret))
	if err != nil {
		return "", errors.New("ErrorReason_ServerBusy")
	}
	return signedToken, nil
}

func verify(c *gin.Context) {
	strToken := c.Param("token")
	claim, err := verifyToken(strToken)
	if err != nil {
		c.String(http.StatusNotFound, err.Error())
		return
	}
	c.String(http.StatusOK, "verify,", claim.UserName)
}

func verifyToken(strToken string) (*jwtClaims, error) {
	// 采集器使用内部token，因此
	if inner_token == strToken{
		return nil,nil
	}
	token, err := jwt.ParseWithClaims(strToken, &jwtClaims{}, func(token *jwt.Token) (interface{}, error) {
		return []byte(Secret), nil
	})
	if err != nil {
		return nil, errors.New("ErrorReason_ServerBusy")
	}
	claims, ok := token.Claims.(*jwtClaims)
	if !ok {
		return nil, errors.New("ErrorReason_ReLogin")
	}
	if err := token.Claims.Valid(); err != nil {
		return nil, errors.New("ErrorReason_ReLogin")
	}
	return claims, nil
}

func validUser(user *model.User) bool {
	return database.DBConn.IsValidUser(user)
}
