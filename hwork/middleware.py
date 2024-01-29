import datetime

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        with open("userActivity.log",'a') as log_file:
            username = request.user.username if request.user.is_authenticated else 'Anonymous'
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_file.write(f'{time}|{username}|URL={request.get_full_path()}\n' )

        return response
