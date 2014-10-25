module("iblib", package.seeall)

function playlist(opt)
    local blank = resource.create_colored_texture(0, 0, 0, 0)

    local current_item
    local next_item

    local switch_time = opt.switch_time

    -- state vars
    local fade_start
    local preload_start
    local progress

    local state = "initial"

    local loader_opt = opt.loader_opt or {
        loop = false,
    }

    local function draw(...)
        local now = sys.now()
        -- print("state -> ", state)

        if state == "initial" then
            has_next, next_item = opt.get_next_item()
            if not has_next then
                print("no initial item")
                return
            end
            state = "load_initial"
            load_start = now
        end
        
        if state == "load_initial" then
            if next_item.file.load(loader_opt) then
                next_item.load_time = now - load_start
                fade_start = now
                state = "wait_fade"
            end
        end

        if state == "getnext" then
            has_next, next_item = opt.get_next_item()
            if not has_next then
                print("no item")
                return
            else
                state = "wait"
                fade_start = now + current_item.duration - switch_time
                preload_start = fade_start - (next_item.load_time or 0)
            end
        end

        if state == "wait" then
            if now > preload_start then
                state = "preload"
            end
        end

        if state == "preload" then
            state = "loading"
            load_start = now
        end
        
        if state == "loading" then
            if next_item.file.load(loader_opt) then
                next_item.load_time = now - load_start
                state = "wait_fade"
            end
        end
        
        if state == "wait_fade" then
            if now > fade_start then
                print("delta fade: ", now - fade_start)
                -- re-adjust. now might have passed fade_start for various reasons:
                -- unexpected loading times, inactive node, ...
                fade_start = now 
                state = "crossfade"
            end
        end
        
        if state == "crossfade" then
            local fade_time = now - fade_start
            progress = fade_time / switch_time
            if progress > 1 then
                progress = 1
            end
            if fade_time > switch_time then
                state = "unload"
            end
        end

        if state == "unload" then
            if current_item and current_item ~= next_item then
                current_item.file.unload()
            end
            current_item = next_item
            opt.playback_started(current_item)
            next_item = nil
            state = "getnext"
        end

        -- Drawing
        local current_surface = blank
        if current_item then
            current_surface = current_item.file.get_surface()
        end

        if state == "crossfade" then
            local next_surface = blank
            if next_item then
                next_surface = next_item.file.get_surface()
            end
            opt.fade(current_surface, next_surface, progress, ...)
        else
            opt.draw(current_surface, ...)
        end
    end

    return {
        draw = draw;
        set_switch_time = function(time)
            switch_time = time
        end;
        get_current_item = function()
            return current_item
        end;
    }
end

