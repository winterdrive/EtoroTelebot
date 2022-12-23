local key = KEYS[1]
local seconds = ARGV[1]
local value = ARGV[2]
redis.call('SETEX',key,seconds,value)


local key = KEYS[1]
local upper = ARGV[1]
local lower = ARGV[2]
local value = ARGV[3]
local myList = redis.call('ZRANGEBYSCORE',key,lower,upper,'LIMIT', 0, 100)  
for i,v in pairs(myList) do
    redis.call('ZADD',key,value,v)  
end 
return myList