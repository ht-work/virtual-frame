package main

import (
	"encoding/json"
	"fmt"
)

func main(){
	a := NewA()
	b,_ := json.Marshal(a)
	fmt.Println(string(b))
}

type A struct {
	Name string
	Age int
}

func NewA() *A {
	return &A{
		"Hello",
		10,
	}
}