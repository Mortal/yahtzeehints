import json

from django.views.generic import View
from django.http import JsonResponse
from django import forms
from django.conf import settings

import yahtzeevalue


KEYS = "PDTVQWsSCH?!123456"


def get_database():
    try:
        return get_database.db
    except AttributeError:
        pass
    get_database.db_wrapper = yahtzeevalue.Database(settings.YAHTZEE_PATH)
    get_database.db = get_database.db_wrapper.__enter__()
    return get_database.db


class HintForm(forms.Form):
    state = forms.CharField()
    roll_count = forms.IntegerField()
    roll = forms.CharField()

    def clean_state(self):
        try:
            state_dict = json.loads(self.cleaned_data["state"])
        except ValueError:
            raise forms.ValidationError("Invalid JSON")
        if not isinstance(state_dict, dict):
            raise forms.ValidationError("Invalid state (should be dict)")
        state = 0
        side_sum = 0
        i = 1
        for k in KEYS:
            try:
                v = state_dict.pop(k)
            except KeyError:
                pass
            else:
                state += i
                if k in "123456":
                    side_sum += v
            i *= 2
        if state_dict:
            raise forms.ValidationError("Unknown keys: %r" % sorted(state_dict))
        state += i * min(side_sum, 84)
        return state

    def clean_roll_count(self):
        roll_count = self.cleaned_data["roll_count"]
        return min(max(roll_count, 1), 3)

    def clean_roll(self):
        roll = self.cleaned_data["roll"]
        if len(roll) != 6:
            raise forms.ValidationError("roll should have length 6")
        if not all(c in "123456" for c in roll):
            raise forms.ValidationError("roll should be digits between 1 and 6")
        return [int(v) for v in roll]


class Hint(View):
    def get(self, request):
        form = HintForm(data=request.GET)
        if form.errors:
            return JsonResponse({"errors": form.errors})
        state = form.cleaned_data["state"]
        roll = form.cleaned_data["roll"]
        roll_count = form.cleaned_data["roll_count"]
        if roll_count == 1:
            response = JsonResponse({"keep_first": get_database().keep_first(state, roll)})
        elif roll_count == 2:
            response = JsonResponse({"keep_second": get_database().keep_second(state, roll)})
        else:
            response = JsonResponse({"best_action": KEYS[get_database().best_action(state, roll)]})
        response["Access-Control-Allow-Origin"] = "*"
        return response
