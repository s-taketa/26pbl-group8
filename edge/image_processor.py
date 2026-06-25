class ImageProcessor:
    # カメラ映像の取得と、NoIRカメラ特有の青みを補正する処理

    def captureImage(self):
        # カメラで画像をキャプチャする
        pass
    
    def correctBlueShift(self, image):
        # NoIRカメラ用の青み補正(RGB入れ替え)
        pass

    def saveImage(self, image, filename=None):
        # キャプチャした画像を一時保存
        pass