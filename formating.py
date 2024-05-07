import json
def format_wallets(wallet):
    wltSting = str(wallet)
    formatedWallet = wltSting[:5] + '...' + wltSting[-5:]
    return formatedWallet
def serialize_inline_keyboard(markup):
    serialized_buttons = []
    for row in markup.keyboard:
        serialized_row = []
        for button in row:
            # Serialize each button to a dictionary, considering only properties you use
            button_dict = {
                'text': button.text,
                'callback_data': getattr(button, 'callback_data', None),
                'url': getattr(button, 'url', None)
            }
            serialized_row.append(button_dict)
        serialized_buttons.append(serialized_row)
    return json.dumps(serialized_buttons, sort_keys=True)


    
