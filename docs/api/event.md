Event configuration
===================

    {
        "event": {
            "title": "Unsere tolle Online-Konferenz",
        },
        "rooms": [
            {
                "name": "Plenum",
                "description": "Hier findet die Eröffnungs- und End-Veranstaltung statt",
                "picture": "https://via.placeholder.com/150",
                "access": [
                    {
                        "level": "viewer",
                        "required_groups": "*"
                    },
                    {
                        "level": "moderator",
                        "required_groups": "moderator_plenum"
                    }
                ],
                "modules": [
                    {
                        "type": "livestream.native",
                        "config": {
                            "hls_url": "https://s1.live.pretix.eu/test/index.m3u8"
                        }
                    },
                    {
                        "type": "chat.matrix",
                        "config": {
                            "matrix_url": "https://matrix.stayseated.tld"
                        }
                    },
                    {
                        "type": "agenda.pretalx",
                        "config": {
                            "matrix_url": "https://pretalx.com/conf/online/schedule/export/schedule.json"
                        }
                    }
                ]
            },
            {
                "name": "Gruppenraum 1",
                "description": "Hier findet die Eröffnungs- und End-Veranstaltung statt",
                "picture": "https://via.placeholder.com/150",
                "access": [
                    {
                        "level": "viewer",
                        "required_groups": "*"
                    },
                    {
                        "level": "moderator",
                        "required_groups": "moderator_plenum"
                    }
                ],
                "modules": [
                    {
                        "type": "call.bigbluebutton",
                        "config": {
                            "bbb_join_url": "https://s1.live.pretix.eu/test/index.m3u8"
                        }
                    }
                ]
            }
        ]
    }