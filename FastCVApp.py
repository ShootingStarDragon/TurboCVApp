#so that main and subprocesses have access to this
import cv2 
import time

def open_kivy(*args):
    from kivy.app import App
    from kivy.lang import Builder
    from kivy.uix.screenmanager import ScreenManager, Screen
    from kivy.graphics.texture import Texture
    from kivy.clock import Clock
    import mediapipe as mp

    class MainApp(App):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            #remember that the KV string IS THE ACTUAL FILE AND MUST BE INDENTED PROPERLY TO THE LEFT!
            self.KV_string = '''
<FCVA_screen_manager>:
    id: FCVA_screen_managerID
    StartScreen:
        id: start_screen_id
        name: 'start_screen_name'
        manager: 'FCVA_screen_managerID'

<StartScreen>:
    id: start_screen_id
    BoxLayout:
        orientation: 'vertical'
        Image:
            id: image_textureID
        Label:
            text: "hello world!"

FCVA_screen_manager: #remember to return a root widget
'''
        def build(self):
            self.title = "Fast CV App Example v0.1.0 by Pengindoramu"
            build_app_from_kv = Builder.load_string(self.KV_string)
            return build_app_from_kv
        
        def on_start(self):
            #start blitting, get the fps as an option [todo]. 1/30 still works because it will always blit the latest image from open_appliedcv subprocess, but kivy itself will be at 30 fps
            Clock.schedule_interval(self.blit_from_shared_memory, 1/30)
        
        def on_request_close(self, *args):
            Clock.unschedule(self.blit_from_shared_memory)
            print("#kivy subprocess closed END!", flush=True)

        def run(self):
            '''Launches the app in standalone mode.
            reference: 
            how to run kivy as a subprocess (so the main code can run neural networks like mediapipe without any delay)
            https://stackoverflow.com/questions/31458331/running-multiple-kivy-apps-at-same-time-that-communicate-with-each-other
            '''
            self._run_prepare()
            from kivy.base import runTouchApp
            runTouchApp()
            self.shared_metadata_dictVAR["kivy_run_state"] = False
        
        def blit_from_shared_memory(self, *args):
            shared_analysis_dict = self.shared_analysis_dictVAR
            if len(shared_analysis_dict) > 0:
                max_key = max(shared_analysis_dict.keys())
                frame = shared_analysis_dict[max_key]
                buf = frame.tobytes()
                #texture documentation: https://github.com/kivy/kivy/blob/master/kivy/graphics/texture.pyx
                #blit to texture
                #blit buffer example: https://stackoverflow.com/questions/61122285/kivy-camera-application-with-opencv-in-android-shows-black-screen
                texture1 = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr') 
                texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                App.get_running_app().root.get_screen('start_screen_name').ids["image_textureID"].texture = texture1
                #after blitting delete some key/value pairs if dict has more than 5 frames:
                if len(shared_analysis_dict) > 5:
                    min_key = min(shared_analysis_dict.keys())
                    del shared_analysis_dict[min_key]

    class FCVA_screen_manager(ScreenManager):
        pass

    class StartScreen(Screen):
        pass

    MainApp.shared_analysis_dictVAR = args[0]
    MainApp.shared_metadata_dictVAR = args[1]
    # MainApp.source = args[2]
    MainApp().run()

def open_media(*args):
    try:
        shared_metadata_dict = args[0]
        frame_rate = args[1]
        print("what is framerate?", frame_rate, flush=True)
        cap = cv2.VideoCapture(args[2])

        prev = time.time()
        while True:
            if "kivy_run_state" in shared_metadata_dict.keys(): 
                if shared_metadata_dict["kivy_run_state"] == False:
                    break
            if "mp_ready" in shared_metadata_dict.keys():
                time_elapsed = time.time() - prev
                if time_elapsed > 1./frame_rate:
                    time_og = time.time()
                    ret, frame = cap.read()
                    time_2 = time.time()
                    prev = time.time()

                    # read the latest frame here and stuff it in the shared memory for open_appliedcv to manipulate
                    if ret:
                        shared_metadata_dict["latest_cap_frame"] = frame
                    # print("cv2 .read() takes long???", time_2 - time_og, 1./frame_rate, flush= True)
    except Exception as e:
        print("read function died!", e, flush=True)

def open_appliedcv(*args):
    try:
        shared_analysis_dict = args[0]
        shared_metadata_dict = args[1]
        appliedcv = args[2]
        shared_metadata_dict["mp_ready"] = True

        while True:
            if "kivy_run_state" in shared_metadata_dict.keys(): 
                if shared_metadata_dict["kivy_run_state"] == False:
                    break
            if "kivy_run_state" and "latest_cap_frame" in shared_metadata_dict.keys():
                if shared_metadata_dict["kivy_run_state"] == False:
                    print("are u breaking?", flush=True)
                    break
                #actually do your cv function here and stuff it in shared_analysis_dict shared memory. You might have to flip the image because IIRC opencv is up to down, left to right, while kivy is down to up, left to right. in any case cv2 flip code 0 is what you want most likely is vertical flip so it's a flip on up down axis while preserving horizontal axis.
                shared_analysis_dict[1] = appliedcv(shared_metadata_dict["latest_cap_frame"],shared_analysis_dict ,shared_metadata_dict)
                # print("why is this so fast? fps:", len(shared_analysis_dict),  flush= True)
    except Exception as e:
        print("open_appliedcv died!", e)

class FCVA():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_int = 0
        self.originpy = None
        self.appliedcv = None
        #put the imports here so that all users have to do is import FCVA and instantiate it in the top level
    
    def run(self):
        if __name__ == "FastCVApp":
            import multiprocessing as FCVA_mp
            #this is so that only 1 window is run when packaging with pyinstaller
            FCVA_mp.freeze_support() 
            shared_mem_manager = FCVA_mp.Manager()
            #shared_analysis_dict holds the actual frames
            shared_analysis_dict = shared_mem_manager.dict()
            #shared_metadata_dict holds keys about run states so things don't error by reading something that doesn't exist
            shared_metadata_dict = shared_mem_manager.dict()
            #set metadata kivy_run_state to true so cv subprocess will run and not get an error by reading uninstantiated shared memory.
            shared_metadata_dict["kivy_run_state"] = True
            
            #read just to get the fps
            source = "media/pexels-cottonbro-7791121 720p.mp4"
            video = cv2.VideoCapture(source)
            fps = video.get(cv2.CAP_PROP_FPS)

            read_subprocess = FCVA_mp.Process(target=open_media, args=(shared_metadata_dict, fps, source))
            read_subprocess.start()

            if self.appliedcv != None:
                cv_subprocess = FCVA_mp.Process(target=open_appliedcv, args=(shared_analysis_dict,shared_metadata_dict, self.appliedcv)) 
                cv_subprocess.start()
            elif self.appliedcv == None:
                print("FCVA.appliedcv is currently None. Not starting the CV subprocess.")
            else:
                print("FCVA.appliedcv block failed")

            kivy_subprocess = FCVA_mp.Process(target=open_kivy, args=(shared_analysis_dict,shared_metadata_dict))
            kivy_subprocess.start()

            #this try except block holds the main process open so the subprocesses aren't cleared when the main process exits early.
            while "kivy_run_state" in shared_metadata_dict.keys():
                if shared_metadata_dict["kivy_run_state"] == False:
                    #when the while block is done, close all the subprocesses using .join to gracefully exit
                    read_subprocess.join()
                    cv_subprocess.join()
                    video.release()
                    kivy_subprocess.join()
                    break
                try:
                    pass 
                except Exception as e:
                    print("Error in run, make sure stream is set. Example: app.source = cv2.VideoCapture(0)", e)
