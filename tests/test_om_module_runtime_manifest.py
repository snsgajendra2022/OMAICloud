from om_ai.runtime.evolution_matrix import module_runtime_manifest


def test_module_manifest_exposes_all_five_om_modules():
    manifest = module_runtime_manifest(native_ready=True)

    assert manifest["runtime"] == "native_om_shared_checkpoint"
    assert manifest["native_model_ready"] is True
    assert [module["id"] for module in manifest["modules"]] == [
        "OM-L1", "OM-L2", "OM-L3", "OM-L4", "OM-L5"
    ]
    assert [module["name"] for module in manifest["modules"]] == [
        "OM Pulse · Chat",
        "OM Mind · Reason",
        "OM Forge · Agent",
        "OM Nova · Create",
        "OM Matrix · Orchestrate",
    ]


def test_modules_are_explicitly_native_and_do_not_claim_quality_from_load():
    for ready in (False, True):
        manifest = module_runtime_manifest(native_ready=ready)
        assert manifest["quality_status"] == "not_certified"
        assert all(module["execution"]["backend"] == "om_native" for module in manifest["modules"])
        assert all(module["execution"]["shared_checkpoint"] is True for module in manifest["modules"])
        assert all(module["execution"]["model_ready"] is ready for module in manifest["modules"])
        assert all(module["execution"]["quality_status"] == "not_certified" for module in manifest["modules"])


def test_module_profiles_have_distinct_roles():
    modules = module_runtime_manifest()["modules"]
    profiles = {module["id"]: module["runtime_profile"] for module in modules}

    assert profiles["OM-L1"]["style"] == "chatbot"
    assert profiles["OM-L2"]["prefer_reasoning"] is True
    assert profiles["OM-L3"]["prefer_tools"] is True
    assert profiles["OM-L4"]["prefer_research"] is True
    assert profiles["OM-L5"]["prefer_planning"] is True
