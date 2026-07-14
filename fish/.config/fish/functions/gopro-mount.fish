# 4. mount the GoPro SD card and print its path
function gopro-mount
    # already mounted? just report where
    for m in /run/media/$USER/* /media/$USER/*
        if test -d "$m/DCIM"
            echo $m
            return 0
        end
    end

    # removable exfat/vfat partitions, most recently attached first
    set -l parts (lsblk -nrpo PATH,TYPE,RM,FSTYPE | string replace -rf '^(\S+) part 1 (exfat|vfat)$' '$1')

    if test -z "$parts"
        echo "gopro-mount: no removable exfat/vfat card found — is it plugged in?" >&2
        return 1
    end

    for part in $parts
        # skip anything already mounted elsewhere; it isn't the card we want
        if findmnt -n "$part" >/dev/null 2>&1
            continue
        end

        set -l mnt (udisksctl mount -b "$part" 2>/dev/null |
            string replace -rf '^Mounted .* at (.*?)\.?$' '$1')

        if test -z "$mnt"
            echo "gopro-mount: failed to mount $part" >&2
            continue
        end

        if test -d "$mnt/DCIM"
            echo $mnt
            return 0
        end

        # not a GoPro card — leave the system as we found it
        udisksctl unmount -b "$part" >/dev/null 2>&1
    end

    echo "gopro-mount: found a card but no DCIM/ on it" >&2
    return 1
end
