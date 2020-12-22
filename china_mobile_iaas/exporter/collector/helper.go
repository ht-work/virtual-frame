package collector

import (
	. "exporter/models"
	"fmt"
)

func getVCPUType()string{
	return "VCPU"
}

func getMemType()string{
	return "MEM"
}

func getIDField()string{
	return "id"
}

func getTypeField()string{
	return "type"
}

func getAppField()string{
	return "app"
}

func getTenantField()string{
	return "tenant"
}

func getRPField()string{
	return "rp"
}

//资源相关的标签名称以及对应的取值
func getDeviceLabelNames()[]string{
	names := []string{
		getIDField(),
		getTypeField(),
		getAppField(),
		getTenantField(),
		getRPField(),
	}
	return names
}
func getDeviceLabelValues(dm *DeviceMetric)[]string{
	m := dm.CMDB
	if( m == nil){
		fmt.Printf("get device label value null : %+v", m);
		return nil
	}
	values := []string{
		m.ID,
		m.Type,
		m.AppId,
		m.TenantId,
		m.RPId,
	}
	return values
}

//业务系统相关的标签名称以及对应的取值
func getAppLabelNames()[]string{
	names := []string{
		getTypeField(),
		getAppField(),
		getTenantField(),
		getRPField(),
	}
	return names
}
func getAppLabelNamesForAppAssignRatio()[]string{
	//没有类型标签
	return getAppLabelNames()[1:]
}
func getAppLabelValues(m *AppMetric, typeValue string)[]string{
	values := []string{
		typeValue,
		m.Quota.AppInfo.ID,
		m.Quota.AppInfo.Tenant,
		m.Quota.AppInfo.RP,
	}
	if typeValue == ""{
		values = []string{
			m.Quota.AppInfo.ID,
			m.Quota.AppInfo.Tenant,
			m.Quota.AppInfo.RP,
		}
	}
	return values
}

//资源池相关的标签名称以及对应的取值
func getRPLabelNames()[]string{
	names := []string{
		getTypeField(),
		getRPField(),
	}
	return names
}
func getRPLabelValues(m *RpMetric, typeValue string)[]string{
	values := []string{
		typeValue,
		m.Quota.ID,
	}
	return values
}
