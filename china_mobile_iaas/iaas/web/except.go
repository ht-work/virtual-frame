package web

import "net/http"

const (
	StatusOk     = 0    //success
	ServerErr    = 1000 // 系统错误
	NotFoundErr  = 1001 // 401错误
	UnknownErr   = 1002 // 未知错误
	ParameterErr = 1003 // 参数错误
	AuthErr      = 1004 // 错误

)

// api错误的结构体
type APIException struct {
	Code int    `json:"code"`
	Msg  string `json:"msg,omitempty"`
	Err  error  `json:"err_msg,omitempty"`
}

// 实现接口
func (e *APIException) Error() string {
	return e.Msg
}

func newAPIException(code int, msg string) *APIException {
	return &APIException{
		Code: code,
		Msg:  msg,
	}
}

func StatsOk(message string) *APIException {
	return newAPIException(StatusOk, message)
}

// 500 错误处理
func ServerError() *APIException {
	return newAPIException(ServerErr, http.StatusText(http.StatusInternalServerError))
}

// 404 错误
func NotFound() *APIException {
	return newAPIException(NotFoundErr, http.StatusText(http.StatusNotFound))
}

// 未知错误
func UnknownError(message string) *APIException {
	return newAPIException(http.StatusForbidden, message)
}

// 参数错误
func ParameterError(message string) *APIException {
	return newAPIException(ParameterErr, message)
}

func UnauthorizedError(message string) *APIException {
	return newAPIException(AuthErr, message)
}
