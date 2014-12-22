hosted_init()

if sys.version and sys.version > "0.8.0" then
    gl.setup(NATIVE_WIDTH, NATIVE_HEIGHT)
else
    gl.setup(1920, 1080)
end

local iblib = require "iblib"

local function make_blender(blend_src)
    local function create_shader(main_src)
        local src = [[
            uniform sampler2D Texture;
            varying vec2 TexCoord;
            uniform vec4 Color;
            uniform float progress;

            float blend(float x) {
                ]] .. blend_src .. [[
            }
            void main() {
                ]] .. main_src .. [[
            }
        ]]
        return resource.create_shader(src)
    end
    local s1 = create_shader[[
        gl_FragColor = texture2D(Texture, TexCoord) * vec4(1.0 - blend(progress));
    ]]
    local s2 = create_shader[[
        gl_FragColor = texture2D(Texture, TexCoord) * vec4(blend(progress));
    ]]
    return function(c, n, progress, x1, y1, x2, y2)
        s1:use{ progress = progress }
        util.draw_correct(c, x1, y1, x2, y2)
        s2:use{ progress = progress }
        util.draw_correct(n, x1, y1, x2, y2)
        s2:deactivate()
    end
end

local faders = {
    crossfade = function(c, n, progress, x1, y1, x2, y2)
        util.draw_correct(c, x1, y1, x2, y2, 1.0 - progress)
        util.draw_correct(n, x1, y1, x2, y2, progress)
    end;

    move = function(c, n, progress, x1, y1, x2, y2)
        local xx = WIDTH * progress
        util.draw_correct(c, x1 + xx, y1, x2 + xx, y2, 1.0 - progress)
        util.draw_correct(n, x1 - WIDTH + xx, y1, x2 - WIDTH + xx, y2, progress)
    end;

    move_shrink = function(c, n, progress, x1, y1, x2, y2)
        local xx = WIDTH * progress
        util.draw_correct(c, x1 + xx, y1, x2, y2, 1.0 - progress)
        util.draw_correct(n, x1 - WIDTH + xx, y1, x2 - WIDTH + xx, y2, progress)
    end;

    flip = function(c, n, progress, x1, y1, x2, y2)
        local xx = WIDTH * progress
        gl.pushMatrix()
            gl.translate(WIDTH/2, HEIGHT/2)
            gl.rotate(progress * 90, 0, 1, 0)
            gl.translate(-WIDTH/2, -HEIGHT/2)
            util.draw_correct(c, x1 + xx, y1, x2, y2, 1.0 - progress)
        gl.popMatrix()

        gl.pushMatrix()
            gl.translate(WIDTH/2, HEIGHT/2)
            gl.rotate(90 - progress * 90, 0, 1, 0)
            gl.translate(-WIDTH/2, -HEIGHT/2)
            util.draw_correct(n, x1 - WIDTH + xx, y1, x2 - WIDTH + xx, y2, progress)
        gl.popMatrix()
    end;

    blend1 = make_blender[[
        x = 1.0 - clamp(TexCoord.x - 1.0 + x * 3.0, 0.0, 1.0);
        return 2.0 * x * x * x - 3.0 * x * x + 1.0;
    ]],

    blend2 = make_blender[[
        x = 1.0 - clamp(TexCoord.y - 1.0 + x * 3.0, 0.0, 1.0);
        return 2.0 * x * x * x - 3.0 * x * x + 1.0;
    ]],

    blend3 = make_blender[[
        vec2 center = vec2(0.5, 0.5);
        vec2 c = TexCoord - center;
        float angle = atan(c.x, c.y) / 3.1415926536;
        float dist = length(c);
        x = abs(mod(angle + dist * 5.0 + x, 2.0) - 1.0) + dist - 2.0 + x * 4.0;
        x = 1.0 - clamp(x, 0.0, 1.0);
        return 2.0 * x * x * x - 3.0 * x * x + 1.0;
    ]],

    blend4 = make_blender[[
        float y = sin( (TexCoord.x - 0.5) * x * 4.0) * sin( (TexCoord.y - 0.5) * x * 4.0);
        return clamp(y - 1.0 + x * 4.0, 0.0, 1.0);  
    ]],

    blend5 = make_blender[[
        return clamp(distance(TexCoord, vec2(0.5, 0.5)) - 1.0 + x * 3.0, 0.0, 1.0);
    ]],

    blend6 = make_blender[[
        return 1.0 - (2.0 * x * x * x - 3.0 * x * x + 1.0);
    ]],
}

local title_start = 99999999

local idx = 0 -- offset before first item. will be incremented during first get_next_item
local playlist_source = function()
    return CONFIG.playlist
end;

local player = iblib.playlist{
    get_next_item = function()
        local playlist = playlist_source()
        idx = idx + 1
        if idx > #playlist then
            idx = 1
        end

        local item = playlist[idx]

        if not item then
            return false, nil
        end

        return true, item
    end;

    switch_time = CONFIG.switch_time,

    fade = function(...)
        title_start = sys.now() + 1.0
        return faders[CONFIG.fade](...)
    end;

    draw = util.draw_correct;

    playback_started = function(current_item)
        pp(current_item)
    end
}

node.event("config_update", function()
    player.set_switch_time(CONFIG.switch_time)
end)

function node.render()
    CONFIG.background_color.clear()

    player.draw(0, 0, WIDTH, HEIGHT)

    if CONFIG.show_title then
        local now = sys.now()
        if now > title_start then
            local in_title = now - title_start
            local alpha = 1.0
            if in_title < 0.5 then
                alpha = in_title * 2
            elseif in_title > CONFIG.title_duration then
                alpha = 0
            elseif in_title > CONFIG.title_duration - 0.5 then
                alpha = 1.0 - (in_title - CONFIG.title_duration + 0.5) * 2
            end
            CONFIG.title_font:write(
                10, HEIGHT - CONFIG.title_size - 5, 
                player.get_current_item().title,
                CONFIG.title_size,
                1, 1, 1, alpha
            )
        end
    end
end
