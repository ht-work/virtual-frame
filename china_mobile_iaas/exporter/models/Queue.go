package models

import (
	"errors"
	"fmt"
	"sync"
)

//循环队列长度
const DefaultQueueSize = 1001

type QElemType *PermMetric

/*
   队列长度的计算公式： 参考《大话数据结构》
   队列满时，还有一个空闲位置（主要是为了区别空队列和满队列）参考《大话数据结构》
*/
//循环队列存储结构
type MyQueue struct {
	data  []QElemType
	front int
	rear  int
	Cap	  int
	mu sync.Mutex
}

//初始化队列，头尾指针都为0
func (q *MyQueue)InitQueue(size int) {
	q.front = 0
	q.rear = 0
	q.Cap = size
	if size == 0 {
		q.Cap = DefaultQueueSize
	}
	q.data = make([]QElemType, q.Cap)
}

//计算队列的长度
func (q *MyQueue)Length() (len int) {
	len = (q.rear - q.front + q.Cap) % q.Cap
	return
}

func (q *MyQueue)isFull()bool{
	if (q.rear+1)%q.Cap == q.front%q.Cap {
		return true
	}else{
		return false
	}
}
func (q *MyQueue)isEmpty()bool{
	if q.rear == q.front {
		return true
	}else{
		return false
	}
}
//入队操作
func (q *MyQueue)EnQueue(e QElemType) (err error) {
	q.mu.Lock()
	defer q.mu.Unlock()
	if q.isFull() {
		err = errors.New(fmt.Sprintf("队列已满！len:%d\n", q.Length()))
		return err
	}
	q.data[q.rear] = e
	q.rear = (q.rear + 1) % q.Cap //循环，不然会越界
	return nil
}
//出队列
func (q *MyQueue)DeQueue() (err error, res QElemType) {
	q.mu.Lock()
	defer q.mu.Unlock()
	if q.isEmpty() {
		err = errors.New("队列为空，没有数据出队列")
		return err,nil
	}
	res = q.data[q.front]
	q.data[q.front]=nil//清空数据
	q.front = (q.front + 1) % q.Cap//数据出队列之后，指针移动到即将出队列的元素位置
	return nil,res
}

