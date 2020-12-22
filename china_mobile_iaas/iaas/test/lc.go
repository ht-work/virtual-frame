package main

import (
	"fmt"
	"time"
)

type Tst struct {
	ch chan int
}

func main() {
	t := Tst{make(chan int,100)}
	go func() {
		for i := 0; i <= 10; i++ {
			t.ch <- i
		}
		close(t.ch)
	}()

	for i := range t.ch {
		time.Sleep(1 * time.Second)
		fmt.Println(i)
	}

}
