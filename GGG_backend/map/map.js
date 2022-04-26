; (function ($) {

    // We'll insert the map after this element:
    var prev_el_selector = '.form-row.field-border';

    // The input elements we'll put lat/lon into and use
    // to set the map's initial lat/lon.
    var lat_input_selector = '#id_border';

    // If we don't have a lat/lon in the input fields,
    // this is where the map will be centered initially.
    var initial_lat = 51.516448,
        initial_lon = -0.130463;

    // Initial zoom level for the map.
    var initial_zoom = 6;

    // Initial zoom level if input fields have a location.
    var initial_with_loc_zoom = 12;

    // Global variables. Nice.
    var map, marker, $lat, $lon;

    /**
     * Create HTML elements, display map, set up event listeners.
     */
    function initMap() {
        var $prevEl = $(prev_el_selector);

        if ($prevEl.length === 0) {
            // Can't find where to put the map.
            return;
        };

        $lat = $(lat_input_selector);
        var has_initial_loc = ($lat.val() && $lon.val());

        if (has_initial_loc) {
            // There is lat/lon in the fields, so centre the map on that.
            initial_lat = parseFloat($lat.val());
            initial_lon = parseFloat($lon.val());
            initial_zoom = initial_with_loc_zoom;
        };

        $prevEl.after($('<div class="js-setloc-map setloc-map"></div>'));

        var mapEl = document.getElementsByClassName('js-setloc-map')[0];

        map = new TMap.Map(mapEl, {
            zoom: 12, // 设置地图缩放级别
            center: new TMap.LatLng(39.984104, 116.307503) // 设置地图中心点坐标
        });
  
        // 初始化几何图形及编辑器
        editor = new TMap.tools.GeometryEditor({
            map, // 编辑器绑定的地图对象
            overlayList: [ // 可编辑图层
                {
                    //GeometryEditor 以 MultiPolygon（可以理解为多边形图层）激活进行编辑
                    id: 'polygon133',
                    overlay: new TMap.MultiPolygon({
                        map
                    }),
                }
            ],
            actionMode: TMap.tools.constants.EDITOR_ACTION.DRAW, //编辑器的工作模式
            snappable: true // 开启邻近吸附
        });
        // 监听绘制结束事件，获取绘制几何图形
        editor.on('draw_complete', (geometry) => {
            console.log(geometry);
        });
    }
    

    /**
     * Re-position marker and set input values.
     */
    function setMarkerPosition(lat, lon) {
        marker.setPosition({ lat: lat, lng: lon });
        setInputValues(lat, lon);
    };

    /**
     * Set both lat and lon input values.
     */
    function setInputValues(lat, lon) {
        setInputValue($lat, lat);
        setInputValue($lon, lon);
    };

    /**
     * Set the value of $input to val, with the correct decimal places.
     * We work out decimal places using the <input>'s step value, if any.
     */
    function setInputValue($input, val) {
        // step should be like "0.000001".
        var step = $input.prop('step');
        var dec_places = 0;

        if (step) {
            if (step.split('.').length == 2) {
                dec_places = step.split('.')[1].length;
            };

            val = val.toFixed(dec_places);
        };

        $input.val(val);
    };

    $(document).ready(function () {
        initMap();
    });

})(django.jQuery);