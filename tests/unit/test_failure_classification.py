"""Unit tests for failure classification types."""

from __future__ import annotations

import dataclasses

import pytest

from justpipe.failures import (
    FailureClassificationConfig,
    FailureClassificationContext,
    FailureKind,
    FailureReason,
    FailureSource,
)


class TestFailureClassificationContext:
    def test_construction_with_all_fields(self) -> None:
        err = ValueError("boom")
        ctx = FailureClassificationContext(
            error=err,
            kind=FailureKind.STEP,
            reason=FailureReason.STEP_ERROR,
            step="my_step",
            default_source=FailureSource.USER_CODE,
        )
        assert ctx.error is err
        assert ctx.kind is FailureKind.STEP
        assert ctx.reason is FailureReason.STEP_ERROR
        assert ctx.step == "my_step"
        assert ctx.default_source is FailureSource.USER_CODE

    def test_construction_with_none_defaults(self) -> None:
        ctx = FailureClassificationContext(
            error=None,
            kind=FailureKind.INFRA,
            reason=FailureReason.INTERNAL_ERROR,
            step=None,
            default_source=FailureSource.FRAMEWORK,
        )
        assert ctx.error is None
        assert ctx.step is None

    def test_frozen_immutability(self) -> None:
        ctx = FailureClassificationContext(
            error=None,
            kind=FailureKind.VALIDATION,
            reason=FailureReason.VALIDATION_ERROR,
            step=None,
            default_source=FailureSource.USER_CODE,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            ctx.step = "changed"  # type: ignore[misc]


class TestFailureClassificationConfig:
    def test_default_values(self) -> None:
        cfg = FailureClassificationConfig()
        assert cfg.source_classifier is None
        assert cfg.external_dependency_prefixes == ()

    def test_custom_source_classifier(self) -> None:
        def my_classifier(ctx: FailureClassificationContext) -> FailureSource | None:
            return FailureSource.EXTERNAL_DEP

        cfg = FailureClassificationConfig(source_classifier=my_classifier)
        assert cfg.source_classifier is my_classifier

    def test_custom_external_dependency_prefixes(self) -> None:
        cfg = FailureClassificationConfig(
            external_dependency_prefixes=("httpx.", "boto3."),
        )
        assert cfg.external_dependency_prefixes == ("httpx.", "boto3.")

    def test_frozen_immutability(self) -> None:
        cfg = FailureClassificationConfig()
        with pytest.raises(dataclasses.FrozenInstanceError):
            cfg.source_classifier = lambda ctx: None  # type: ignore[misc]


class TestFailureSourceClassifier:
    def test_callable_as_classifier(self) -> None:
        def classifier(ctx: FailureClassificationContext) -> FailureSource | None:
            return FailureSource.EXTERNAL_DEP if ctx.step == "call_api" else None
        api_ctx = FailureClassificationContext(
            error=ConnectionError("timeout"),
            kind=FailureKind.STEP,
            reason=FailureReason.STEP_ERROR,
            step="call_api",
            default_source=FailureSource.USER_CODE,
        )
        other_ctx = FailureClassificationContext(
            error=ValueError("bad input"),
            kind=FailureKind.STEP,
            reason=FailureReason.STEP_ERROR,
            step="validate",
            default_source=FailureSource.USER_CODE,
        )
        assert classifier(api_ctx) is FailureSource.EXTERNAL_DEP
        assert classifier(other_ctx) is None
