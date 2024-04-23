from config import *

def refresh_pool():
  for refresh_pool in conn.listAllStoragePools():
    refresh_pool.refresh(0)

def get_pool_list():
   list_pools = []
   for pools in conn.listStoragePools():
      pool = conn.storagePoolLookupByName(pools)
      list_pools.append(pool.name())
   return list_pools

def get_full_pool():
     refresh_pool()
     list_pool_full = []
     for pools in get_pool_list():
        pool_info = get_pool_info(pools)
        pool_info.append(get_pool_volumes(pools))
        list_pool_full.append(pool_info)
     return list_pool_full

# Name,UUID,Active,Total,Used,Free,Percent
def get_pool_info(pool_name):
    refresh_pool()
    pool_info = []
    pool = conn.storagePoolLookupByName(pool_name)
    pool_info.append(pool.name())
    pool_info.append(pool.UUIDString())
    pool_info.append(str(pool.isActive()))
    pool_info.append(str(human_size(pool.info()[1])))
    pool_info.append(str(human_size(pool.info()[2])))
    pool_info.append(str(human_size(pool.info()[3])))
    if pool.info()[1]==0:
        pool_info.append(str(0))
    else:
        pool_info.append(str(round((pool.info()[2]*100)/pool.info()[1],2)))
    return pool_info

#Name,Total,Used,Percent
def get_pool_volumes(pool_name):
    refresh_pool()
    volumes_list = []
    pool = conn.storagePoolLookupByName(pool_name)
    for volume in pool.listVolumes():
        volume_info=[]
        vol = pool.storageVolLookupByName(volume)
        volume_info.append(volume)
        volume_info.append(human_size(vol.info()[1]))
        volume_info.append(human_size(vol.info()[2]))
        if vol.info()[1]==0:
             vol_used=0
        else:
             vol_used=round((vol.info()[2]*100)/vol.info()[1],2)
        volume_info.append(vol_used)
        volumes_list.append(volume_info)
    return volumes_list

def del_pool_vol(pool_name,volume_name):
    refresh_pool()
    pools=conn.storagePoolLookupByName(pool_name)
    vlm=pools.storageVolLookupByName(volume_name)
    vlm.delete()
