package main

import (
	"fmt"
	"github.com/gin-gonic/gin"
)

func (p *App) FindAllResource(ctx *gin.Context) {
	fmt.Println(ctx)
}

func (p *App) FindResource(ctx *gin.Context) {
	fmt.Println(ctx)
}

func (p *App) FindAllResourcePool(ctx *gin.Context) {

}

func (p *App) FindAllBizSys(ctx *gin.Context) {

}

func (p *App) FindAllTenant(ctx *gin.Context) {

}
