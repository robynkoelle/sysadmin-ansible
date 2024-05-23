#!/bin/bash

echo -e "\e[36mNetwork interfaces:\e[0m"
ip addr show
echo

router_ip="192.168.2.1"
subnet_prefix="192.168.2."
is_router=false
if ip addr show | grep -q "$router_ip"; then
  is_router=true
fi

function find_subnet_ips() {
  local subnet=$1
  local timeout=$2
  local ips=($(nmap -sn $subnet --host-timeout $timeout | grep -oP '^Nmap scan report for .*?\K(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'))
  echo "${ips[@]}"
}

function test_ip() {
  local ip=$1

  # Ping test
  if ping -c 1 "$ip" &>/dev/null; then
    echo -e "Ping: \e[32mOK\e[0m"
  else
    echo -e "Ping: \e[32mFAILED\e[0m"
  fi

  # Check if the ip is reached via the router
  if ! $is_router && ! [[ $ip =~ ^$subnet_prefix ]]; then
    output=$(ip route get "$ip")
    if echo "$output" | grep -q "via $router_ip"; then
         echo -e "Reached via router: \e[32mOK\e[0m"
    else
         echo -e "Reached via router: \e[31mFAILED\e[0m"
         echo -e "Output:\n$output"
    fi
  fi

  # Test port 22 (ssh)
  if timeout 3 telnet "$ip" 22 </dev/null &>/dev/null; then
    echo -e "Telnet 22: \e[32mOK\e[0m"
  else
    echo -e "Telnet 22: \e[31mFAILED\e[0m"
  fi
}

function test_subnet() {
  local subnet=$1

  echo "Finding IPs in $subnet..."
  local subnet_ips
  subnet_ips=$(find_subnet_ips "$subnet" "1s")
  echo -e "Done\n"

  for ip in $subnet_ips; do
    echo "$ip:"
    test_ip "$ip"
    echo
  done
}

function get_status_code() {
  local url=$1
  local result
  result=$(wget --spider -S "$url" --timeout 5 2>&1 | grep "^  HTTP/" | tail -n 1 | awk '{print $2}')
  echo "$result"
}

subnets=(
  192.168.1.0/24
  192.168.2.0/24
  192.168.3.0/24
  192.168.4.0/24
  192.168.5.0/24
  192.168.6.0/24
  192.168.7.0/24
  192.168.8.0/24
  192.168.9.0/24
  192.168.10.0/24
)

for subnet in "${subnets[@]}"; do
  echo -e "\e[36mTesting connections to subnet $subnet\e[0m"
  test_subnet "$subnet"
done

echo -e "\e[36mFirewall configuration:\e[0m"
iptables -S
echo

echo -e "\e[36mCan surf internet:\e[0m"
echo -e "curl google.com..."
if [ "$(get_status_code 'https://google.com')" == "200" ]; then
    echo -e "\e[32mOK\e[0m"
else
    echo -e "\e[31mFAILED\e[0m"
fi

echo -e "\e[36mCannot surf internet without proxy:\e[0m"
echo -e "curl google.com..."
response=$(https_proxy='' http_proxy='' get_status_code 'https://google.com')
if  [ -z "$response" ]; then
    echo -e "\e[32mOK\e[0m"
else
    echo -e "\e[31mFAILED\e[0m"
fi

echo -e "\e[36mCan use DNS:\e[0m"
if dig +time=5 +tries=1 google.com +short | grep -q .; then
    echo -e "\e[32mOK\e[0m"
else
    echo -e "\e[31mFAILED\e[0m"
fi
