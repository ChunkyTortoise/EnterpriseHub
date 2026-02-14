# Bare Except Clause Audit Report

## Summary
- **Total Files with Issues:** 184
- **Total Bare Except Clauses:** 322

## Priority Files (Most Issues)


### `services/claude_orchestrator.py` (8 issues)

**Line 450:** `except Exception:`
```python
                    # Convert to Gemini/Claude tool declaration format
                    try:
                        parameters = mcp_tool.model_json_schema()
                    except Exception:
                        # Fallback for complex schemas that Pydantic V2 fails to serialize for JSON Schema
                        parameters = {"type": "object", "properties": {}}

```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 825:** `except Exception:`
```python
                enhanced["semantic_memory"] = memory_context.get("relevant_knowledge", "")
                enhanced["conversation_history"] = memory_context.get("conversation_history", [])
                enhanced["extracted_preferences"] = memory_context.get("extracted_preferences", {})
            except Exception:
                # Graceful degradation if memory unavailable
                pass

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 1219:** `except Exception:`
```python

            return actions

        except Exception:
            return []

    def _structure_action(self, action_text: str) -> Dict[str, Any]:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 1319:** `except Exception:`
```python

            return variants

        except Exception:
            return []

    def _parse_risk_factors(self, content: str, json_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 1375:** `except Exception:`
```python

            return risks

        except Exception:
            return []

    def _structure_risk(self, risk_text: str) -> Dict[str, str]:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 1454:** `except Exception:`
```python

            return opportunities

        except Exception:
            return []

    def _structure_opportunity(self, opp_text: str) -> Dict[str, str]:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 1609:** `except Exception:`
```python

                    validated_messages.append({"role": role_str, "content": content_str})

                except Exception:
                    # Skip individual malformed messages
                    continue

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 1615:** `except Exception:`
```python

            return validated_messages

        except Exception:
            # Graceful degradation on any error
            return []

```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/semantic_response_caching.py` (7 issues)

**Line 244:** `except:`
```python
        if OPENAI_AVAILABLE:
            try:
                return OpenAIEmbeddingService()
            except:
                pass

        if SENTENCE_TRANSFORMERS_AVAILABLE:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 250:** `except:`
```python
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                return SentenceTransformerEmbeddingService()
            except:
                pass

        # Fallback to mock service
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 261:** `except:`
```python
        if REDIS_AVAILABLE:
            try:
                return CacheService()
            except:
                pass

        # Fallback to in-memory dict
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 352:** `except:`
```python
                cached_data = await self.cache_backend.get(cache_key)
                if cached_data:
                    return CachedResponse(**json.loads(cached_data))
            except:
                pass

        return None
```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 380:** `except:`
```python
                        cached_data = await self.cache_backend.get(cached_key)
                        if cached_data:
                            best_match = CachedResponse(**json.loads(cached_data))
                    except:
                        continue

        return best_match, best_similarity
```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 404:** `except:`
```python
        else:
            try:
                await self.cache_backend.set(cache_key, json.dumps(asdict(cached_response), default=str), ttl=ttl)
            except:
                pass

        # Add to similarity index
```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 457:** `except:`
```python
            try:
                # Clear Redis keys with semantic prefix
                await self.cache_backend.delete_pattern("semantic_*")
            except:
                pass

    async def get_similar_queries(self, query_text: str, limit: int = 10) -> List[Tuple[str, float]]:
```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/enhanced_lead_scorer.py` (6 issues)

**Line 241:** `except:`
```python
        try:
            ml_result = self.ml_scorer.score_lead(lead_id, lead_data, include_explanation=True)
            ml_score = ml_result.score
        except:
            ml_score = None

        # Create unified result
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 342:** `except:`
```python
            if not self.fallback_manager.is_circuit_open("ml_scorer"):
                ml_result = self.ml_scorer.score_lead(lead_id, lead_data, include_explanation=True)
                ml_score = ml_result.score
        except:
            self.fallback_manager.record_failure("ml_scorer")

        # Try dynamic scoring
```

**Suggested Fix:** `except (IOError, FileNotFoundError) as e:`

**Line 351:** `except:`
```python
                dynamic_result = await self.dynamic_orchestrator.score_lead_with_dynamic_weights(
                    tenant_id=tenant_id, lead_id=lead_id, lead_data=lead_data, segment=segment
                )
        except:
            self.fallback_manager.record_failure("dynamic_scorer")

        # Combine available scores intelligently
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 372:** `except:`
```python
        if failed_mode == ScoringMode.DYNAMIC_ADAPTIVE:
            try:
                return await self._score_ml_enhanced(lead_id, context, tenant_id, segment)
            except:
                pass

        if failed_mode in [ScoringMode.DYNAMIC_ADAPTIVE, ScoringMode.ML_ENHANCED]:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 378:** `except:`
```python
        if failed_mode in [ScoringMode.DYNAMIC_ADAPTIVE, ScoringMode.ML_ENHANCED]:
            try:
                return await self._score_jorge_original(lead_id, context, tenant_id, segment)
            except:
                pass

        # Final fallback - static heuristics
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 547:** `except:`
```python
                # Simple budget parsing
                budget_str = str(budget_str).replace("$", "").replace(",", "").replace("k", "000")
                budget = float(budget_str)
            except:
                budget = 0

        # Convert to lead_data format
```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/advanced_property_matching_engine.py` (6 issues)

**Line 517:** `except Exception:`
```python

            return min(complexity, 1.0)

        except Exception:
            return 0.5  # Moderate complexity default

    async def _predict_engagement(
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 572:** `except Exception:`
```python

            return min(max(conversion, 0.0), 1.0)

        except Exception:
            return engagement_prediction * 0.7  # Conservative fallback

    def _determine_presentation_strategy(
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 602:** `except Exception:`
```python
            # Default to value-focused
            return PresentationStrategy.VALUE_FOCUSED

        except Exception:
            return PresentationStrategy.STREAMLINED

    async def _generate_behavioral_reasoning(
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 647:** `except Exception:`
```python
            else:
                return "Property matches search criteria with standard behavioral profile."

        except Exception:
            return "Behavioral analysis provides additional match insights."

    async def _calculate_ml_confidence(
```

**Suggested Fix:** `except (IOError, FileNotFoundError) as e:`

**Line 677:** `except Exception:`
```python

            return min(max(confidence, 0.1), 0.95)

        except Exception:
            return 0.7  # Default confidence

    async def _get_optimal_presentation_time(self, behavioral_prediction: Any) -> Optional[str]:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 694:** `except Exception:`
```python

            return None

        except Exception:
            return None

    async def _get_cached_matches(
```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/voice_ai_integration.py` (6 issues)

**Line 182:** `except:`
```python
        if HAS_AUDIO_LIBS:
            try:
                self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
            except:
                logger.warning("WebRTC VAD not available")

    def detect_speech(self, audio_data: bytes) -> bool:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 190:** `except:`
```python
        if self.vad and len(audio_data) == self.frame_size * 2:  # 16-bit samples
            try:
                return self.vad.is_speech(audio_data, self.sample_rate)
            except:
                pass

        # Fallback: simple energy-based detection
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 804:** `except:`
```python
            if line.startswith("BUYING_INTENT:"):
                try:
                    result["buying_intent"] = int(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("URGENCY:"):
                try:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 809:** `except:`
```python
            elif line.startswith("URGENCY:"):
                try:
                    result["urgency"] = int(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("ENGAGEMENT:"):
                try:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 814:** `except:`
```python
            elif line.startswith("ENGAGEMENT:"):
                try:
                    result["engagement"] = int(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("OBJECTION_LIKELIHOOD:"):
                try:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 819:** `except:`
```python
            elif line.startswith("OBJECTION_LIKELIHOOD:"):
                try:
                    result["objection_likelihood"] = int(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("KEY_INSIGHTS:"):
                result["insights"] = line.split(":", 1)[1].strip()
```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/dynamic_scoring_weights.py` (6 issues)

**Line 307:** `except Exception:`
```python
                    profile = self._deserialize_profile(profile_data)
                    self.config_cache[cache_key] = profile
                    return profile
            except Exception:
                pass  # Fall back to default

        # Use default profile
```

**Suggested Fix:** `except (IOError, FileNotFoundError) as e:`

**Line 514:** `except Exception:`
```python
                            or datetime.fromisoformat(test_config.end_date) > datetime.now()
                        ):
                            return test_config
            except Exception:
                pass

        return None
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 577:** `except Exception:`
```python
                self.redis_client.lpush(list_key, json.dumps(outcome_data))
                self.redis_client.ltrim(list_key, 0, 999)  # Keep last 1000
                self.redis_client.expire(list_key, 86400 * 30)  # 30 days
            except Exception:
                pass  # Continue without Redis

    async def _get_performance_data(self, tenant_id: str, segment: LeadSegment) -> List[Dict]:
```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 598:** `except:`
```python
                for item in data:
                    try:
                        performance_data.append(json.loads(item))
                    except:
                        continue

                # Cache locally
```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 604:** `except Exception:`
```python
                # Cache locally
                self.performance_history[history_key] = performance_data
                return performance_data
            except Exception:
                pass

        return []
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 625:** `except Exception:`
```python
            }

            self.redis_client.set(cache_key, json.dumps(profile_data), ex=86400)  # 24 hours
        except Exception:
            pass  # Continue without Redis

    def _deserialize_profile(self, profile_data: Dict) -> WeightProfile:
```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`


### `api/routes/bi_websocket_routes.py` (6 issues)

**Line 93:** `except:`
```python
        logger.error(f"Dashboard WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 144:** `except:`
```python
        logger.error(f"Revenue Intelligence WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 201:** `except:`
```python
        logger.error(f"Bot Performance WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 257:** `except:`
```python
        logger.error(f"Business Intelligence WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 316:** `except:`
```python
        logger.error(f"AI Concierge WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 375:** `except:`
```python
        logger.error(f"Advanced Analytics WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


```

**Suggested Fix:** `except Exception as e:` + add logging


### `deployment/rollback_manager.py` (5 issues)

**Line 736:** `except Exception:`
```python
            # This would integrate with health check endpoints
            logger.info("Health check validation passed")
            return True
        except Exception:
            return False

    async def _validate_database(self) -> bool:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 745:** `except Exception:`
```python
            # Test database connection
            logger.info("Database validation passed")
            return True
        except Exception:
            return False

    async def _validate_cache(self) -> bool:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 754:** `except Exception:`
```python
            # Test Redis connection
            logger.info("Cache validation passed")
            return True
        except Exception:
            return False

    async def _validate_application(self) -> bool:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 763:** `except Exception:`
```python
            # Test application endpoints
            logger.info("Application validation passed")
            return True
        except Exception:
            return False

    async def _validate_performance(self) -> bool:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 772:** `except Exception:`
```python
            # Test performance metrics
            logger.info("Performance validation passed")
            return True
        except Exception:
            return False

    async def _cleanup_old_rollback_points(self):
```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/claude_assistant.py` (5 issues)

**Line 394:** `except Exception:`
```python
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass

        return {"content": response.content}
```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 972:** `except:`
```python
                return "750k_1m"
            else:
                return "over_1m"
        except:
            return "unknown"

    def _normalize_location(self, zip_code: str) -> str:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 1078:** `except Exception:`
```python
                # Store in L1 cache for next access
                self.embeddings_cache[text_hash] = embedding
                return embedding
        except Exception:
            pass

        # Compute new embedding
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 1189:** `except Exception:`
```python
                            "response": data,
                        }
                    )
            except Exception:
                continue

        return matches
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 1225:** `except Exception:`
```python
                            best_similarity = similarity
                            best_match = {"similarity": similarity, "response": data.get("response")}

                except Exception:
                    continue

            return best_match
```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/client_success_integration_service.py` (5 issues)

**Line 519:** `except:`
```python
            # Test basic functionality
            test_result = await self.transaction_intelligence.get_proactive_recommendations({"test": "transaction"})
            return test_result is not None
        except:
            return False

    async def _test_ai_negotiation_connection(self) -> bool:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 528:** `except:`
```python
            # Test basic functionality
            test_result = await self.ai_negotiation.analyze_negotiation_opportunity({"test": "data"})
            return test_result is not None
        except:
            return False

    async def _test_market_service_connection(self) -> bool:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 536:** `except:`
```python
        try:
            test_result = await self.market_service.get_current_market_conditions()
            return test_result is not None
        except:
            return False

    async def _test_claude_integration(self) -> bool:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 544:** `except:`
```python
        try:
            test_response = await self.claude.generate_response("Test connection", "test")
            return bool(test_response)
        except:
            return False

    async def _test_ghl_integration(self) -> bool:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 552:** `except:`
```python
        try:
            test_result = await self.ghl_client.get_contacts(limit=1)
            return test_result is not None
        except:
            return False

    async def _setup_event_handlers(self) -> None:
```

**Suggested Fix:** `except Exception as e:` + add logging


### `streamlit_demo/components/claude_cost_tracking_dashboard.py` (5 issues)

**Line 109:** `except:`
```python
        try:
            if hasattr(self.conversation_optimizer, "get_optimization_stats"):
                return await self.conversation_optimizer.get_optimization_stats()
        except:
            pass
        return {"tokens_saved": 2847563, "avg_reduction": 52.3, "conversations_optimized": 1247}

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 118:** `except:`
```python
        try:
            if hasattr(self.prompt_caching, "get_cache_analytics"):
                return await self.prompt_caching.get_cache_analytics()
        except:
            pass
        return {"hit_rate": 94.2, "cost_saved": 1247.83, "cache_entries": 8934, "avg_savings_per_hit": 0.14}

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 127:** `except:`
```python
        try:
            if hasattr(self.token_budget, "get_budget_analytics"):
                return await self.token_budget.get_budget_analytics()
        except:
            pass
        return {"utilization": 67.3, "active_budgets": 23, "alerts_active": 2, "cost_savings": 234.67}

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 136:** `except:`
```python
        try:
            if hasattr(self.async_service, "get_performance_stats"):
                return await self.async_service.get_performance_stats()
        except:
            pass
        return {"avg_response_time": 127.5, "throughput_improvement": 3.2, "parallel_operations": 1834}

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 145:** `except:`
```python
        try:
            if hasattr(self.db_service, "get_pool_metrics"):
                return await self.db_service.get_pool_metrics()
        except:
            pass
        return {"active_connections": 8, "pool_utilization": 34.7, "avg_connection_time": 23.4}

```

**Suggested Fix:** `except Exception as e:` + add logging


### `streamlit_demo/jorge_delivery_dashboard.py` (4 issues)

**Line 46:** `except Exception:`
```python

        summary = asyncio.run(_analytics_service.get_daily_summary("all"))
        return summary.get("total_messages", 0) > 0
    except Exception:
        return False


```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 218:** `except Exception:`
```python
                "Warm": warm,
                "Cold": cold,
            }
    except Exception:
        pass
    return None

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 281:** `except Exception:`
```python
        summary = asyncio.run(_analytics_service.get_daily_summary("all"))
        if summary.get("total_messages", 0) > 0:
            return summary
    except Exception:
        pass
    return None

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 327:** `except Exception:`
```python
        temps = metrics.get("seller", {}).get("temp_breakdown", {})
        if sum(temps.values()) > 0:
            return {"Hot": temps.get("hot", 0), "Warm": temps.get("warm", 0), "Cold": temps.get("cold", 0)}
    except Exception:
        pass
    return None

```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/streamlit_performance_optimizer.py` (4 issues)

**Line 297:** `except Exception:`
```python
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb < limit_mb
        except Exception:
            return True  # Allow rendering if we can't check memory

    def _memory_monitor(self, component_name: str):
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 313:** `except Exception:`
```python
                try:
                    process = psutil.Process()
                    self.start_memory = process.memory_info().rss / 1024 / 1024
                except Exception:
                    self.start_memory = 0
                return self

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 377:** `except Exception:`
```python
        """Get current Streamlit session ID."""
        try:
            return st.session_state.get("session_id", "default")
        except Exception:
            return "default"

    # LAZY LOADING UTILITIES
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 561:** `except Exception:`
```python
                "current_memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "memory_percent": round(process.memory_percent(), 2),
            }
        except Exception:
            memory_info = {"current_memory_mb": 0, "memory_percent": 0}

        return {
```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/claude_executive_intelligence.py` (4 issues)

**Line 53:** `except Exception:`
```python
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"market_sentiment": "Unknown", "raw_analysis": content}


```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 95:** `except Exception:`
```python
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"performance_score": 0, "raw_analysis": content}


```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 137:** `except Exception:`
```python
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"pipeline_health": "Unknown", "raw_analysis": content}


```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`

**Line 182:** `except Exception:`
```python
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"executive_summary": "Analysis failed", "raw_analysis": content}


```

**Suggested Fix:** `except (json.JSONDecodeError, ValueError) as e:`


### `analytics/predictive_models.py` (4 issues)

**Line 544:** `except Exception:`
```python
            future_df = pd.DataFrame({"ds": [future_date]})
            forecast = self.prophet_model.predict(future_df)
            return forecast["yhat"].iloc[0]
        except Exception:
            return 0.0

    def _xgb_predict_single(self, features: Dict[str, float]) -> float:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 563:** `except Exception:`
```python
            # Make prediction
            prediction = self.xgb_model.predict(scaled_features)
            return prediction[0]
        except Exception:
            return 0.0

    def get_feature_importance(self) -> Dict[str, float]:
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 574:** `except Exception:`
```python
        try:
            importance_scores = self.xgb_model.feature_importances_
            return dict(zip(self.feature_columns, importance_scores))
        except Exception:
            return {}


```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 799:** `except Exception:`
```python

            importance_scores = self.model.feature_importances_
            return dict(zip(selected_feature_names, importance_scores))
        except Exception:
            return {}


```

**Suggested Fix:** `except Exception as e:` + add logging


### `streamlit_demo/components/project_copilot.py` (4 issues)

**Line 23:** `except Exception:`
```python
        try:
            companion = get_claude_platform_companion()
            companion_available = True
        except Exception:
            companion = None
            companion_available = False

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 55:** `except Exception:`
```python
                        asyncio.set_event_loop(loop)
                        greeting = run_async(companion.generate_project_greeting("Jorge"))
                        greeting_text = greeting
                    except Exception:
                        pass

            st.session_state.claude_greeting_text = greeting_text
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 127:** `except Exception:`
```python
    try:
        companion = get_claude_platform_companion()
        companion_available = True
    except Exception:
        companion = None
        companion_available = False

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 152:** `except:`
```python
                        asyncio.set_event_loop(loop)
                        guidance = run_async(companion.get_hub_guidance(current_hub))
                        st.info(guidance)
                    except:
                        st.info(
                            f"The {current_hub} is optimized for Phase 6 operations. Focus on your high-intent leads."
                        )
```

**Suggested Fix:** `except Exception as e:` + add logging


### `streamlit_demo/jorge_unified_bot_dashboard.py` (3 issues)

**Line 50:** `except:`
```python

        try:
            return asyncio.run(coro)
        except:
            return None


```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 142:** `except:`
```python
                    "hot_leads_generated": lead_data.get("immediate_priority", 0),
                    "pipeline_conversion": 34.7,
                }
            except:
                pass

        # Fallback mock data
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 175:** `except:`
```python
                    "voice_handoffs": seller_data.get("handoffs", 0),
                    "conversion_to_listing": 42.3,
                }
            except:
                pass

        # Fallback mock data
```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/luxury_market_data_integration.py` (3 issues)

**Line 588:** `except Exception:`
```python
            if score_match:
                return min(float(score_match.group()), 100.0)

        except Exception:
            pass

        # Fallback calculation
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 786:** `except Exception:`
```python
                },
            }

        except Exception:
            # Fallback competitive analysis
            return {
                "market_gaps": ["Technology differentiation", "Premium service automation"],
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 934:** `except Exception:`
```python
        try:
            response = await self.claude.generate_claude_response(prompt, "market_insights")
            return response
        except Exception:
            return f"""
            Rancho Cucamonga Luxury Market Executive Summary:

```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/celebration_engine.py` (3 issues)

**Line 571:** `except:`
```python
                    # Fallback to template if AI fails
                    if not message or len(message) > 200:
                        message = template["message"]
                except:
                    message = template["message"]

            return CelebrationContent(
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 870:** `except:`
```python
            personalized = await self.claude.generate_response(personalization_prompt)
            return personalized if personalized and len(personalized) <= 150 else base_message

        except:
            return base_message

    async def _personalize_countdown_message(
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 891:** `except:`
```python
            personalized = await self.claude.generate_response(personalization_prompt)
            return personalized if personalized and len(personalized) <= 150 else base_message

        except:
            return base_message

    async def _encourage_social_sharing(
```

**Suggested Fix:** `except Exception as e:` + add logging


### `services/language_detection.py` (3 issues)

**Line 107:** `except Exception:`
```python
            )
            self._pipeline_loaded = True
            logger.info("XLM-RoBERTa language detection model loaded")
        except Exception:
            self._load_failed = True
            logger.warning(
                "Failed to load XLM-RoBERTa model; using heuristic fallback"
```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 172:** `except Exception:`
```python
                is_code_switching=secondary is not None,
                secondary_language=secondary,
            )
        except Exception:
            logger.warning("Model inference failed; falling back to heuristic")
            return self._detect_heuristic(text)

```

**Suggested Fix:** `except Exception as e:` + add logging

**Line 187:** `except Exception:`
```python
            try:
                result = self._pipeline(sentence[:512])
                languages.add(result[0]["label"])
            except Exception:
                continue

        if len(languages) >= 2:
```

**Suggested Fix:** `except Exception as e:` + add logging

