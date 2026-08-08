from controllers.asset import AssetDownloadAuthorize, AssetDownloadLog, AssetUploadComplete, AssetUploadTarget


class AssetRoutes(object):

    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "assets/upload-target/",
            view_func=AssetUploadTarget.as_view("asset_upload_target"),
            methods=["POST"],
            endpoint="should_be_v1_only_asset_upload_target",
        )
        v1.add_url_rule(
            "assets/<string:asset_uuid>/complete/",
            view_func=AssetUploadComplete.as_view("asset_upload_complete"),
            methods=["POST"],
            endpoint="should_be_v1_only_asset_upload_complete",
        )
        v1.add_url_rule(
            "assets/<string:asset_uuid>/downloads/",
            view_func=AssetDownloadLog.as_view("asset_download_log"),
            methods=["POST"],
            endpoint="should_be_v1_only_asset_download_log",
        )
        v1.add_url_rule(
            "assets/<string:asset_uuid>/deliver/",
            view_func=AssetDownloadAuthorize.as_view("asset_download_authorize"),
            methods=["POST"],
            endpoint="should_be_v1_only_asset_download_authorize",
        )
