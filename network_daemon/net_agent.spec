%define name net_agent
%define version %(grep -m1 __version__ net_agent/__init__.py | awk -F = '{print $2}' | sed "s/'//g")
%define python_path /opt/pipenv/.venv/bin/python3


Summary: A gRPC server for net agent
Name: %{name}
Version: %{version}
Release: 1%{?dist}
Source0: %{name}-%{version}.tar.gz
Autoreq: 0
License: BSD
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: anymous <anymous@example.com>
Url: www.example.com


%description
A gRPC server for agent,provide ovs management, nic management and so on.
release tag: %{release_tag}


%prep
%setup -n %{name}-%{version} -n %{name}-%{version}


%build
%{python_path} setup.py build


%install
%{python_path} setup.py install --no-compile --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%{python_path} -m compileall -b legacy $RPM_BUILD_ROOT
find $RPM_BUILD_ROOT -name "*.py" 2>/dev/null | xargs rm -rf
sed -i 's#\.py$#\.pyc#g' INSTALLED_FILES

_python_path=%{python_path}
path_prefix=${_python_path%/bin/*}
mkdir -p $RPM_BUILD_ROOT/etc/vap
mv net_agent.cfg $RPM_BUILD_ROOT/etc/vap
echo "/etc/vap/net_agent.cfg" >> INSTALLED_FILES

mkdir -p $RPM_BUILD_ROOT/usr/lib/systemd/system
cp net_agent.service $RPM_BUILD_ROOT/usr/lib/systemd/system/
echo "/usr/lib/systemd/system/net_agent.service" >> INSTALLED_FILES

mkdir -p $RPM_BUILD_ROOT/opt/vap/net_agent/acl
echo "/opt/vap/net_agent/acl" >> INSTALLED_FILES

mkdir -p $RPM_BUILD_ROOT/opt/vap/net_agent/qos
echo "/opt/vap/net_agent/qos" >> INSTALLED_FILES

mkdir -p $RPM_BUILD_ROOT/var/log/vap
echo "/var/log/vap" >> INSTALLED_FILES

%preun
if [ $1 -eq 0 ]; then
    # uninstall not upgrade
    systemctl --no-reload disable --now %{name}.service &>/dev/null || :
fi


%postun
if [ $1 -ge 1 ]; then
    # upgrade not uninstall
    systemctl try-restart %{name}.service &>/dev/null || :
fi


%check
find $RPM_BUILD_ROOT -type d -name __pycache__ 2>/dev/null | xargs rm -rf


%clean
rm -rf $RPM_BUILD_ROOT


%files -f INSTALLED_FILES
%defattr(-,root,root)

