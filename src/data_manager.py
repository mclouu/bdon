import json
from pathlib import Path

class DataManager:
    def __init__(self, data_dir="data", cache_dir="cache"):
        self.data_dir = Path(data_dir)
        
        # Gestion du dossier cache dédié
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True) # Crée le dossier s'il n'existe pas
        
        self.collection_path = self.cache_dir / "collection.json"
        
    def load_json(self, filename):
        """Charge un fichier JSON du dossier data en toute sécurité."""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def build_or_update_collection(self, save_file_path):
        """
        Traite le save.json, le croise avec les tables de référence et 
        renvoie un tuple : (total_cartes, nouvelles_cartes_count, a_change)
        """
        # 1. Charger la sauvegarde utilisateur
        with open(save_file_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        
        player_cards = []
        if isinstance(save_data, list):
            for item in save_data:
                if isinstance(item, dict) and "_memberCards" in item:
                    player_cards.extend(item["_memberCards"])
                else:
                    player_cards.append(item)
        else:
            player_cards = save_data.get("_memberCards", [])

        # 2. Charger les tables de référence
        raw_member_cards = self.load_json("member_card.json")
        member_cards_list = raw_member_cards.get("_allData", raw_member_cards) if isinstance(raw_member_cards, dict) else raw_member_cards
        master_cards = {card["_id"]: card for card in member_cards_list}

        characters = {item["_id"]: item.get("_english", "") for item in self.load_json("character_name.json")}
        subtitles = {item["_id"]: item.get("_english", "") for item in self.load_json("member_subtitle.json")}
        
        rarities_map = self.load_json("rarities.json")
        rarity_dict = rarities_map[0]["rarities"] if rarities_map else {}
        
        card_types_map = self.load_json("card_types.json")
        type_dict = card_types_map[0]["cardTypes"] if card_types_map else {}

        def load_skill_dict(filename, prefix):
            data = self.load_json(filename)
            skills_map = {}
            for item in data:
                sid = item.get("_id", "")
                if isinstance(sid, str) and sid.startswith(prefix):
                    try:
                        num_id = int(sid.replace(prefix, ""))
                        skills_map[num_id] = item.get("_english", "")
                    except ValueError:
                        pass
                skills_map[sid] = item.get("_english", "")
            return skills_map

        leader_skills = load_skill_dict("leader_skill_name_description.json", "Leader_Skill_Name_Description_")
        live_skills = load_skill_dict("live_skill_name_description.json", "Live_Skill_Name_Description_")
        gekisou_skills = load_skill_dict("gekisou_skill_description.json", "Gekisou_Skill_Description_")

        compiled_collection = []

        for p_card in player_cards:
            master_id = p_card.get("_masterId")
            master_card = master_cards.get(master_id, {})

            name_text_id = master_card.get("_nameTextID", "")
            subtitle_text_id = master_card.get("_subtitleTextID", "")
            rarity_num = str(master_card.get("_rarity", ""))
            card_type_num = str(master_card.get("_cardType", ""))

            leader_skill_id = master_card.get("_leaderSkillID")
            live_skill_id = master_card.get("_liveSkillID")
            gekisou_skill_id = master_card.get("_gekisouSkillID")

            card_info = {
                "master_id": master_id,
                "exp": p_card.get("_exp"),
                "awake_count": p_card.get("_awakeCount"),
                "rank": p_card.get("_rank"),
                "live_skill_level": p_card.get("_liveSkillLevel"),
                "performance_skill_level": p_card.get("_performanceSkillLevel"),
                "nameTextID": characters.get(name_text_id, name_text_id),
                "subtitleTextID": subtitles.get(subtitle_text_id, subtitle_text_id),
                "characterID": master_card.get("_characterID"),
                "rarity": rarity_dict.get(rarity_num, rarity_num),
                "cardType": type_dict.get(card_type_num, card_type_num),
                "leaderSkill": leader_skills.get(leader_skill_id, ""),
                "liveSkill": live_skills.get(live_skill_id, ""),
                "gekisouSkill": gekisou_skills.get(gekisou_skill_id, "")
            }
            compiled_collection.append(card_info)

        # 3. Comparer avec l'ancien collection.json pour détecter les changements
        old_collection = []
        if self.collection_path.exists():
            try:
                with open(self.collection_path, "r", encoding="utf-8") as f:
                    old_collection = json.load(f)
            except Exception:
                pass

        old_ids = {card["master_id"] for card in old_collection}
        new_ids = {card["master_id"] for card in compiled_collection}
        
        # Calcul des ajouts et des modifications globales
        added_cards = new_ids - old_ids
        added_count = len(added_cards)
        has_changed = (compiled_collection != old_collection)

        # 4. Sauvegarder le nouveau fichier
        with open(self.collection_path, "w", encoding="utf-8") as f:
            json.dump(compiled_collection, f, ensure_ascii=False, indent=2)

        return len(compiled_collection), added_count, has_changed