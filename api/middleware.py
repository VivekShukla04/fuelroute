class CorsHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "accept, authorization, content-type, user-agent, x-csrftoken, x-requested-with"
        response["Access-Control-Allow-Methods"] = "DELETE, GET, OPTIONS, PATCH, POST, PUT"
        response["Access-Control-Max-Age"] = "86400"
        return response
