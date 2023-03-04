#!/usr/bin/env python3
import subprocess as sp
import os
import pwd
os.chdir(os.path.expanduser('~'))
pcre2_version="pcre2-10.40"
zlib_version="zlib-1.2.13"
openssl_version="openssl-1.1.1p"
nginx_version="nginx-1.22.1"
deps = [
   'curl', 'wget', 'tree','perl','perl-devel','perl-ExtUtils-Embed','libxslt','libxslt-devel',
   'libxml2','libxml2-devel','gd','gd-devel','GeoIP','GeoIP-devel'
]
deps_group = ['Development Tools']
def set_download_url(array=[]):
    if not array or not isinstance(array, list):
        return
    return '/'.join(array) + '.tar.gz'

pcre2_download_url=set_download_url([
    'github.com/PCRE2Project/pcre2/releases/download/', pcre2_version, pcre2_version
    ])
zlib_download_url=set_download_url([
    'http://zlib.net/', zlib_version
    ])
openssl_download_url=set_download_url([
    'http://www.openssl.org/source/', openssl_version
    ])
nginx_download_url= set_download_url([
    'https://nginx.org/download/', nginx_version
])

def download_build_install(url):
    tar_file = url.split('/')[-1]
    print(f'Downloading {url} and untaring {tar_file}')
    sp.run(f'wget -N {url}', shell=True)
    sp.run(f'tar xzvf {tar_file}', shell=True)

def delete_tar_gz(version):
    tarfile=version + '.tar.gz'
    print(f'deleting {tarfile}')
    os.remove(os.path.join(os.path.expanduser('~'), tarfile))
    print(f'deleted {tarfile}')

print('ok, first thin first lets get all the dnf dependencies to compile nginx')
print('are you ready for timewasting dnf forever repo loads? [y/n]')
answer = input()
if not answer or answer.lower().startswith('n'):
    print('ok, have a good day')
if answer.lower().startswith('y'):
    new = ['sudo', 'dnf' ]
    groupinstall = new + ['groupinstall', '-y'] + deps_group
    depinstall = new + ['install', '-y'] + deps
    listed = [groupinstall, depinstall]
    for a in listed:
        sp.run(a)
print(f'Nice, now lets download the sources for:\n\t{openssl_version}, {zlib_version},{pcre2_version}')
print('are you ready?[y/n]')
answer1 = input()
if not answer1 or answer1.lower().startswith('n'):
    print('ok, have a good day')
if answer.lower().startswith('y'):
    for b in [openssl_download_url, zlib_download_url, pcre2_download_url]:
        download_build_install(b)
    for c in [openssl_version, zlib_version, pcre2_version]:
        delete_tar_gz(c)
    download_build_install(nginx_download_url)
print(f'setting the man page:')
if not os.path.exists('/usr/share/man/man8/nginx.8'):
    sp.run(['sudo', 'cp', os.path.join(os.path.expanduser('~'),f'{nginx_version}/nginx.8'),  '/usr/share/man/man8'])
    sp.run(['sudo', 'gzip', '/usr/share/man/man8/nginx.8'])
    sp.run('ls /usr/share/man/man8/ | grep nginx.8.gz', shell=True)
print(f'going into {nginx_version} directory')
os.chdir(nginx_version)
sp.run( ['./configure', '--prefix=/etc/nginx',          '--sbin-path=/usr/sbin/nginx',
            '--modules-path=/usr/lib64/nginx/modules',   '--conf-path=/etc/nginx/nginx.conf',
            '--error-log-path=/var/log/nginx/error.log', '--pid-path=/var/run/nginx.pid',
            '--lock-path=/var/run/nginx.lock',           '--user=nginx',
            '--group=nginx', '--build=Fedora',           '--builddir=nginx-1.15.8',
            '--with-select_module', '--with-poll_module',
            '--with-threads',            '--with-file-aio',
            '--with-http_ssl_module',            '--with-http_v2_module',
            '--with-http_realip_module',            '--with-http_addition_module',
            '--with-http_xslt_module=dynamic',            '--with-http_image_filter_module=dynamic',
            '--with-http_geoip_module=dynamic',            '--with-http_sub_module',
            '--with-http_dav_module',            '--with-http_flv_module',
            '--with-http_mp4_module',            '--with-http_gunzip_module',
            '--with-http_gzip_static_module',            '--with-http_auth_request_module',
            '--with-http_random_index_module',            '--with-http_secure_link_module',
            '--with-http_degradation_module',            '--with-http_slice_module',
            '--with-http_stub_status_module',            '--with-http_perl_module=dynamic',
            '--with-perl_modules_path=/usr/lib64/perl5', '--with-perl=/usr/bin/perl',
            '--http-log-path=/var/log/nginx/access.log', '--http-client-body-temp-path=/var/cache/nginx/client_temp',
            '--http-proxy-temp-path=/var/cache/nginx/proxy_temp',
            '--http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp',
            '--http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp',
            '--http-scgi-temp-path=/var/cache/nginx/scgi_temp',
            '--with-mail=dynamic', '--with-mail_ssl_module', '--with-stream=dynamic',
            '--with-stream_ssl_module', '--with-stream_realip_module',
            '--with-stream_geoip_module=dynamic', '--with-stream_ssl_preread_module',
            '--with-compat', f'--with-pcre=../{pcre2_version}',      '--with-pcre-jit',
            f'--with-zlib=../{zlib_version}',           f'--with-openssl=../{openssl_version}',
            '--with-openssl-opt=no-nextprotoneg',            '--with-debug']
)
sp.run('make')
sp.run(['sudo', 'make', 'install'])
if os.path.islink('/etc/nginx/modules'):
    sp.run('sudo rm /etc/nginx/modules', shell=True)

sp.run('sudo ln -s /usr/lib64/nginx/modules /etc/nginx/modules', shell=True)
try:
    pwd.getpwnam('nginx')
except KeyError:
    sp.run('sudo useradd --system --home /var/cache/nginx --shell /sbin/nologin\
        --comment "nginx user" --user-group nginx', shell=True)
for x in ['/var/cache/nginx/client_temp','/var/cache/nginx/fastcgi_temp',
    '/var/cache/nginx/proxy_temp','/var/cache/nginx/scgi_temp','/var/cache/nginx/uwsgi_temp']:
    if not os.path.exists(x):
        sp.run(['sudo','mkdir', '-p', x])
sp.run('sudo chmod 700 /var/cache/nginx/*', shell=True)
sp.run('sudo chown nginx:root /var/cache/nginx/*', shell=True)
print('check for errors')
sp.run(['sudo', 'nginx', '-t'])