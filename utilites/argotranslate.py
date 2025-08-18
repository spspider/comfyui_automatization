import argostranslate.package, argostranslate.translate



def install_language_package(from_code, to_code):
    """Install language package for translation."""
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(lambda p: p.from_code == from_code and p.to_code == to_code, available_packages)
    )
    argostranslate.package.install_from_path(package_to_install.download())

def translate_text(text, from_code, to_code):
    """Translate text from one language to another."""
    install_language_package(from_code, to_code)
    return argostranslate.translate.translate(text, from_code, to_code)

def translateTextBlocks(blocks, tolanguages=("ru", "ro")):
    """Translate text blocks from one language to another."""
    for block in blocks:
        if "text" in block:
            original_text = block["text"]
            block["text"] = {"en": original_text}
            for lang in tolanguages:
                translated_text = translate_text(original_text, "en", lang)
                block["text"][lang] = translated_text
    return blocks

def translate_meta(meta, target_language):
    """Translate all string values in meta dictionary to target language."""
    translated_meta = {}
    for key, value in meta.items():
        if isinstance(value, str):
            translated_meta[key] = translate_text(value, "en", target_language)
        else:
            translated_meta[key] = value
    return translated_meta


if __name__ == "__main__":
    # Example usage
    test_blocks = [{"text": "Hello world!", "duration": 5}]
    translated_blocks = translateTextBlocks(test_blocks, tolanguages=("ru",))
    
    # Now you can access Russian text like this:
    print(translated_blocks[0]['text']['ru'])  # Should print Russian translation
                    
                    
                                      