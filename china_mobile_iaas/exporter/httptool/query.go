package httptool

func sendGetRequest(url string, params map[string]string)([]byte,error){
	obj,err := get(url, params)
	if err != nil{
		return nil,err
	}
	//fmt.Printf("%+v", obj)
	return obj,err
}
