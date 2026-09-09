from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CodingRequest:

    original_request: str

    framework: list[str] = field(
        default_factory=list
    )

    features: list[str] = field(
        default_factory=list
    )

    output_type: str = "code"



class CodingOrchestrator:


    def analyze(
        self,
        message: str
    ) -> CodingRequest:


        request = CodingRequest(
            original_request=message
        )


        text = message.lower()


        # technology extraction
        technologies = [
            "react",
            "vue",
            "angular",
            "flutter",
            "laravel",
            "python"
        ]


        for tech in technologies:

            if tech in text:
                request.framework.append(
                    tech
                )


        # feature understanding

        if "login" in text:

            request.features.append(
                "authentication UI"
            )


        if "dashboard" in text:

            request.features.append(
                "dashboard interface"
            )


        if "ui" in text or "design" in text:

            request.features.append(
                "frontend design"
            )


        return request