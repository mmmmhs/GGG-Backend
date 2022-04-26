; (function ($) {
    // We'll insert the map after this element:
    var prev_el_selector = '.form-row.field-border';

    // The input elements we'll put lat/lon into and use
    // to set the map's initial lat/lon.
    var lat_input_selector = '#id_border';



    // Global variables. Nice.
    var map, editor;

    /**
     * Create HTML elements, display map, set up event listeners.
     */
    function initMap() {
        var $prevEl = $(prev_el_selector);
        var $path = $(lat_input_selector);
        if ($prevEl.length === 0) {
            // Can't find where to put the map.
            return;
        };
        $prevEl.after($('<button type="button" id="toolControl">删除</button><div class="js-setloc-map setloc-map"></div>'));
        $("#toolControl").on('click', (e) => {

                editor.delete();
            
        });
        $("#toolControl").trigger("create");
        var mapEl = document.getElementsByClassName('js-setloc-map')[0];

        console.log(mapEl);
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
            snappable: true,// 开启邻近吸附,
            selectable: true
        });
        // 监听绘制结束事件，获取绘制几何图形
        editor.on('draw_complete', (geometry) => {
            editor.setActionMode(TMap.tools.constants.EDITOR_ACTION.INTERACT)
            $path.val(JSON.stringify(geometry.paths.map(ob=>{return {lat:ob.lat, lng:ob.lng}})));
        });
        editor.on('delete_complete', (geometry) => {
            editor.setActionMode(TMap.tools.constants.EDITOR_ACTION.DRAW)
            $path.val('');
        });
        if ($path.val()) {
            var lay = editor.getActiveOverlay().overlay
            var path = JSON.parse($path.val());
            lay.add([{ paths: path.map(obj => { return new TMap.LatLng(obj.lat, obj.lng) }), styleId: 'default' }])
            editor.setActionMode(TMap.tools.constants.EDITOR_ACTION.INTERACT)
        }
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


    $(document).ready(function () {
        initMap();
    });

})(django.jQuery);