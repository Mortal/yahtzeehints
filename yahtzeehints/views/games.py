import asyncio
import time
import json
from django.views.generic import View
from django.views.generic.edit import BaseFormView
from django.http import JsonResponse
from django import forms
from django.utils import timezone
from channels.generic.http import AsyncHttpConsumer


games = {}


class GameList(View):
    def get(self, request):
        print(games)
        game_list = [
            {"id": key, "name": game["name"]} for key, game in games.items()
        ]
        return JsonResponse({"games": game_list})


class GameCreate(View):
    def post(self, request):
        print(games)
        key = "game%s" % len(games)
        game = games[key] = {"name": "%s" % timezone.now(), "patches": []}
        return JsonResponse({"game": {"id": key, "name": game["name"]}})


class JsonFormView(BaseFormView):
    def get_form_kwargs(self):
        data = self.request.read()
        try:
            decoded = json.loads(data.decode(self.request.encoding))
            form_data = {key: value if isinstance(value, str) else json.dumps(value) for key, value in decoded.items()}
        except (UnicodeDecodeError, ValueError):
            form_data = {}
        return {
            "initial": self.get_initial(),
            "prefix": self.get_prefix(),
            "data": form_data,
        }

    def form_invalid(self, form):
        return JsonResponse({"errors": form.errors})

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class WaitForm(forms.Form):
    game = forms.CharField()
    version = forms.IntegerField()

    def clean_game(self):
        game_id = self.cleaned_data["game"]
        try:
            return games[game_id]
        except KeyError:
            print(games)
            print(repr(game_id))
            raise forms.ValidationError("Unknown game id")


class PatchForm(forms.Form):
    game = forms.CharField()
    version = forms.IntegerField()
    patches = forms.CharField()

    def clean_game(self):
        game_id = self.cleaned_data["game"]
        try:
            return games[game_id]
        except KeyError:
            print(games)
            print(repr(game_id))
            raise forms.ValidationError("Unknown game id")

    def clean_patches(self):
        try:
            patches = json.loads(self.cleaned_data["patches"])
        except ValueError:
            raise forms.ValidationError("Couldn't parse patches as JSON")
        if not isinstance(patches, list):
            raise forms.ValidationError("Patches must be a JSON list")
        return patches


MAX_WAIT_SECONDS = 20
SLEEP_SECONDS = 0.2


class Wait(AsyncHttpConsumer):
    async def handle(self, body):
        print("Wait")
        headers = [
            (b"Content-Type", b"application/json; charset=utf-8"),
        ]
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as e:
            print("wait: Bad data", e, repr(body))
            await self.send_response(200, json.dumps({"error": "Could not read body as UTF-8 JSON"}).encode("utf-8"), headers=headers)
            return
        try:
            form = WaitForm(data=data)
            if not form.is_valid():
                print("wait: Form errors", form.errors)
                await self.send_response(200, json.dumps({"errors": form.errors}).encode("utf-8"), headers=headers)
                return
            await self.send_headers(headers=headers)
            await self.send_body(b"", more_body=True)

            game = form.cleaned_data["game"]["patches"]
            version = form.cleaned_data["version"]
            if len(game) == version:
                print("wait: Nothing new %s" % version)
            for i in range(round(MAX_WAIT_SECONDS / SLEEP_SECONDS)):
                if len(game) != version:
                    break
                await asyncio.sleep(SLEEP_SECONDS)
            patches = [p for v in game[version:] for p in v]
            print("wait: send %s patches" % len(patches))
            await self.send_body(json.dumps({"version": len(game), "patches": patches}).encode("utf-8"))
        except Exception as e:
            print("Wait: Error in processing", e)
            raise


class GamePatch(JsonFormView):
    form_class = PatchForm

    def form_valid(self, form):
        game = form.cleaned_data["game"]["patches"]
        version = form.cleaned_data["version"]
        if len(game) != version:
            patches = [p for v in game[version:] for p in v]
            return JsonResponse({"version": len(game), "patches": patches})
        game.append(form.cleaned_data["patches"])
        return JsonResponse({"version": len(game)})
